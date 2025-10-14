
#!/usr/bin/env python3
from __future__ import annotations
import os
from datetime import datetime, timezone

from caldav2json.config import load_settings
from caldav2json.adapters.ics_codec import IcsCodec
from caldav2json.adapters.json_store import JsonTodoStore
from caldav2json.adapters.caldav_store import RadicaleCalendarStore
from caldav2json.services.sync_service import SyncService
from caldav2json.utils import decode_ics_list, merge_todos, ensure_uid

# Target local todo.json
TODO_PATH = os.path.expanduser("~/.local/state/quickshell/user/todo.json")

def main() -> None:
    start = datetime.now(timezone.utc)
    print(f"[cron] start {start.isoformat().replace('+00:00','Z')}")
    print(f"[cron] local path: {TODO_PATH}")

    cfg = load_settings()
    print(f"[cron] caldav_url={cfg.caldav_url} verify_ssl={cfg.verify_ssl}")
    codec = IcsCodec()
    cal = RadicaleCalendarStore(cfg.caldav_url, cfg.username, cfg.password, cfg.verify_ssl)
    store = JsonTodoStore(TODO_PATH)

    # 1. Fetch remote todos via raw WebDAV listing (includes completed)
    hrefs = cal.debug_list_resource_hrefs()
    remote_blobs = []
    for href in hrefs:
        data = cal.debug_get_ics(href)
        if data:
            remote_blobs.append(data)
    print(f"[cron] remote blobs (PROPFIND): {len(remote_blobs)}")
    remote_todos, decode_errs = decode_ics_list(codec, remote_blobs)

    # --- RAW WEBDAV DIAGNOSTICS: list every .ics and decode them ---
    print("[cron][diag] PROPFIND Depth:1 to enumerate all .ics in collection...")
    hrefs = cal.debug_list_resource_hrefs()
    raw_remote_todos = []
    for i, href in enumerate(hrefs):
        ics = cal.debug_get_ics(href)
        if ics is None:
            continue
        try:
            decoded = codec.from_ics(ics)
            print(f"[cron][diag] {i:03d} {href} -> {len(decoded)} VTODO(s)")
            for t in decoded:
                raw_remote_todos.append(t)
        except Exception as e:
            print(f"[cron][diag] decode ERROR {href}: {e}")


    # 2. Load local todos
    if os.path.exists(TODO_PATH):
        try:
            local_todos = store.load()
            print(f"[cron] local todos loaded: {len(local_todos)}")
        except Exception as e:
            print(f"[cron] ERROR reading local todos: {e}")
            local_todos = []
    else:
        print("[cron] local file not found, assuming empty")
        local_todos = []

    # 3. Merge both sides
    merged = merge_todos(local_todos, remote_todos)

    # 4. Upload merged set back to Radicale — ensure UID present in body
    sync = SyncService(store, cal, codec)
    uploaded_urls = []
    for idx, t in enumerate(merged):
        t = ensure_uid(t, sync.make_uid)
        ics = codec.to_ics([t])
        put_url = f"{cal.calendar_url}{t.uid}.ics" if hasattr(cal, "calendar_url") else "<unknown-url>"
        url = cal.put_vtodo(ics, t.uid)
        uploaded_urls.append(url)

    # 5. Write merged JSON locally
    print(f"[cron] writing local JSON -> {TODO_PATH}")
    store.save(merged)

    end = datetime.now(timezone.utc)
    print(f"[cron] done uploaded={len(uploaded_urls)} duration={(end-start).total_seconds():.2f}s")

if __name__ == "__main__":
    main()
