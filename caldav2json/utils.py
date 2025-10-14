
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Tuple
from .domain import Todo
from .services.sync_service import SyncService

def _ts(dt):
    if not dt:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    if isinstance(dt, datetime):
        return dt.astimezone(timezone.utc).replace(microsecond=0)
    return datetime.fromtimestamp(0, tz=timezone.utc)

def _freshness(t: Todo):
    return max(_ts(getattr(t, "last_modified", None)),
               _ts(getattr(t, "completed", None)),
               _ts(getattr(t, "dtstamp", None)))

def _fmt_dt(dt):
    return _ts(dt).isoformat().replace("+00:00", "Z")

def decode_ics_list(codec, blobs: List[bytes]) -> Tuple[list[Todo], int]:
    todos: list[Todo] = []
    errors = 0
    for i, blob in enumerate(blobs):
        try:
            decoded = codec.from_ics(blob)
            todos.extend(decoded)
        except Exception as e:
            errors += 1
            print(f"[decode] blob#{i}: ERROR {e}")
    print(f"[decode] total todos={len(todos)} errors={errors}")
    return todos, errors

def ensure_uid(t: Todo, make_uid) -> Todo:
    uid = t.uid or make_uid(t.content)
    if t.uid != uid:
        print(f"[uid] fill-in uid for content={t.content!r} -> {uid}")
        return Todo(
            uid=uid,
            content=t.content,
            done=t.done,
            status=t.status,
            percent_complete=t.percent_complete,
            dtstamp=t.dtstamp,
            created=t.created,
            last_modified=t.last_modified,
            completed=t.completed,
            due=t.due,
            description=t.description,
            priority=t.priority,
            categories=t.categories,
        )
    return t

def merge_todos(local: list[Todo], remote: list[Todo]) -> list[Todo]:
    """
    Merge two lists. Prefer newer by (last_modified|completed|dtstamp).
    On ties or unknown recency, prefer done=True to avoid 'unticking'.
    Prefer remote UID if items match by content but UIDs differ.
    """
    by_uid: dict[str, Todo] = {}
    by_hash: dict[str, str] = {}

    def hash_key(t: Todo) -> str:
        return SyncService.make_uid(t.content)

    print(f"[merge] start local={len(local)} remote={len(remote)}")

    # Seed with remote first
    for r in remote:
        uid = r.uid or hash_key(r)
        if uid in by_uid:
            print(f"[merge][remote-dup] uid={uid} keeping first")
        by_uid[uid] = r
        by_hash.setdefault(hash_key(r), uid)

    # Merge local
    for l in local:
        h = hash_key(l)
        uid = l.uid or by_hash.get(h) or h
        if uid not in by_uid:
            by_uid[uid] = l
            by_hash.setdefault(h, uid)
            continue

        r = by_uid[uid]
        r_mod = _freshness(r)
        l_mod = _freshness(l)

        if l_mod > r_mod:
            by_uid[uid] = l
        elif l_mod == r_mod:
            if l.done and not r.done:
                by_uid[uid] = l


    merged = list(by_uid.values())
    print(f"[merge] merged count={len(merged)}")

    # Normalize
    out: list[Todo] = []
    for t in merged:
        st, pc, done = Todo.canonical_status(t.done, t.status, t.percent_complete)
        nt = Todo(
            uid=t.uid or by_hash.get(hash_key(t)) or hash_key(t),
            content=t.content.strip(),
            done=done,
            status=st,
            percent_complete=pc,
            dtstamp=t.dtstamp,
            created=t.created,
            last_modified=t.last_modified,
            completed=t.completed,
            due=t.due,
            description=t.description,
            priority=t.priority,
            categories=t.categories,
        )
        out.append(nt)
    return out





def content_key(t: Todo) -> str:
    # Deterministic key based on SUMMARY, matches SyncService.make_uid(content)
    from .services.sync_service import SyncService
    return SyncService.make_uid(t.content)
