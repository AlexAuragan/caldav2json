
from icalendar import Calendar as ICalendar, Todo as ITodo
from datetime import datetime, timezone, date
from typing import Iterable, List, Optional
from ..domain import Todo

def _iso_trim_z(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None: return None
    return dt.astimezone(timezone.utc).replace(microsecond=0)

class IcsCodec:
    def to_ics(self, todos: Iterable[Todo]) -> bytes:
        cal = ICalendar()
        cal.add("prodid", "-//radatodo//EN")
        cal.add("version", "2.0")
        for t in todos:
            it = ITodo()
            it.add("uid", t.uid)
            it.add("summary", t.content)
            if t.dtstamp:      it.add("dtstamp", _iso_trim_z(t.dtstamp))
            if t.created:      it.add("created", _iso_trim_z(t.created))
            if t.last_modified:it.add("last-modified", _iso_trim_z(t.last_modified))
            if t.completed:    it.add("completed", _iso_trim_z(t.completed))
            if isinstance(t.due, datetime): it.add("due", _iso_trim_z(t.due))
            elif isinstance(t.due, date):   it.add("due", t.due)
            it.add("status", t.status)
            it.add("percent-complete", t.percent_complete)
            if t.description is not None: it.add("description", t.description)
            if t.priority is not None:    it.add("priority", t.priority)
            if t.categories:              it.add("categories", t.categories)
            cal.add_component(it)
        return cal.to_ical()

    def from_ics(self, ics_bytes: bytes) -> List[Todo]:
        out: List[Todo] = []
        cal = ICalendar.from_ical(ics_bytes)
        for comp in cal.walk():
            if getattr(comp, "name", None) != "VTODO":
                continue
            # decoded returns date/datetime
            g = getattr(comp, "decoded", lambda *_: None)
            dtstamp   = g("dtstamp", None)
            created   = g("created", None)
            lastmod   = g("last-modified", None)
            completed = g("completed", None)
            due       = g("due", None)

            uid         = str(comp.get("uid") or "").strip()
            content     = str(comp.get("summary") or "").strip()
            description = (str(comp.get("description")).strip()
                           if comp.get("description") is not None else None)
            status_raw  = str(comp.get("status") or "").strip().upper() or None

            try: pct = int(comp.get("percent-complete"))
            except Exception: pct = None
            try: prio = int(comp.get("priority"))
            except Exception: prio = None

            cats_raw = comp.get("categories")
            if cats_raw is None:
                cats = None
            else:
                try:    cats = [str(x) for x in list(cats_raw.cats)]
                except Exception:
                    try: cats = [str(x) for x in list(cats_raw)]
                    except Exception:
                        cats = [str(cats_raw)]

            st, pc, is_done = Todo.canonical_status(
                done=(completed is not None),
                status=status_raw,
                pct=pct
            )

            out.append(Todo(
                uid=uid,
                content=content,
                done=is_done,
                status=st,
                percent_complete=pc,
                dtstamp=dtstamp,
                created=created,
                last_modified=lastmod,
                completed=completed,
                due=due,
                description=description,
                priority=prio,
                categories=cats,
            ))
        return out
