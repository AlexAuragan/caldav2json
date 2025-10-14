
from icalendar import Calendar as ICalendar
import json
from datetime import datetime, date, timezone

def radicale_to_json(ics_path: str) -> str:
    """
    Read an ICS file and return a JSON dump (string) of VTODOs with rich fields:
    - uid, content (SUMMARY), done, status, percent_complete
    - dtstamp, created, last_modified, completed, due (ISO 8601 strings)
    - description, priority, categories (list[str])
    """
    with open(ics_path, "rb") as f:
        raw = f.read()

    todos = []
    try:
        cal = ICalendar.from_ical(raw)
    except Exception:
        return json.dumps(todos, ensure_ascii=False, indent=2)

    def _iso(v):
        if v is None:
            return None
        # icalendar returns datetime/date via .decoded('prop')
        if isinstance(v, datetime):
            # normalize to Z (UTC) for stable comparisons
            v = v.astimezone(timezone.utc).replace(microsecond=0)
            return v.isoformat().replace("+00:00", "Z")
        if isinstance(v, date):
            return v.isoformat()
        return None

    for comp in cal.walk():
        if getattr(comp, "name", None) != "VTODO":
            continue

        # decoded(...) gracefully returns native datetime/date or bytes.
        dtstamp     = getattr(comp, "decoded", lambda *_: None)("dtstamp", None)
        created     = getattr(comp, "decoded", lambda *_: None)("created", None)
        lastmod     = getattr(comp, "decoded", lambda *_: None)("last-modified", None)
        completed   = getattr(comp, "decoded", lambda *_: None)("completed", None)
        due         = getattr(comp, "decoded", lambda *_: None)("due", None)

        # Text-like fields
        uid         = str(comp.get("uid") or "").strip()
        summary     = str(comp.get("summary") or "").strip()
        description = (str(comp.get("description")).strip()
                       if comp.get("description") is not None else None)
        status      = str(comp.get("status") or "").strip().upper() or None

        # Numbers / enums
        try:
            percent_complete = int(comp.get("percent-complete"))
        except Exception:
            percent_complete = None

        try:
            priority = int(comp.get("priority"))
        except Exception:
            priority = None

        # Categories may be a list-like value
        cats_raw = comp.get("categories")
        if cats_raw is None:
            categories = None
        else:
            try:
                categories = [str(x) for x in list(cats_raw.cats)]
            except Exception:
                try:
                    categories = [str(x) for x in list(cats_raw)]
                except Exception:
                    categories = [str(cats_raw)]

        done = (status == "COMPLETED") or (percent_complete == 100) or (completed is not None)
        if percent_complete is None:
            percent_complete = 100 if done else 0
        if status is None:
            status = "COMPLETED" if done else "NEEDS-ACTION"

        todos.append({
            "uid": uid,
            "content": summary,
            "done": bool(done),
            "status": status,
            "percent_complete": percent_complete,
            "dtstamp": _iso(dtstamp),
            "created": _iso(created),
            "last_modified": _iso(lastmod),
            "completed": _iso(completed),
            "due": _iso(due),
            "description": description,
            "priority": priority,
            "categories": categories,
        })

    return json.dumps(todos, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    dump = radicale_to_json("calendar-export.ics")
    print(dump)
