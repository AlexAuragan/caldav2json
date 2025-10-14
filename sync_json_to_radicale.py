
import os
import json
import hashlib
from datetime import datetime, timezone
from icalendar import Calendar, Todo
import requests

def sync_todos_json_to_caldav(json_path, calendar_url, username, password, output_ics_path=None, verify_ssl=True):
    """
    - json_path: path to todo.json (list of {"content": str, "done": bool})
    - calendar_url: CalDAV collection URL (must end with '/'), e.g.:
        "https://radicale.auragan.fr/admin/89ce9c48-cf96-7cc7-0e82-a0cfbacc735b/"
    - username/password: Radicale auth
    - output_ics_path: if set, writes a merged VCALENDAR containing all VTODOs
    - verify_ssl: passed to requests.* calls
    """
    # Load todos
    with open(json_path, "r", encoding="utf-8") as f:
        todos = json.load(f)

    # Build a merged VCALENDAR (optional write to disk)
    merged = Calendar()
    merged.add("prodid", "-//todo.json->CalDAV//EN")
    merged.add("version", "2.0")

    now = datetime.now(timezone.utc)

    # Ensure collection URL has trailing slash
    if not calendar_url.endswith("/"):
        calendar_url = calendar_url + "/"

    uploaded = []

    for item in todos:
        content = (item.get("content") or "").strip()
        if not content:
            continue  # skip empty lines

        done = bool(item.get("done"))
        uid = "todo-" + hashlib.sha1(content.encode("utf-8")).hexdigest() + "@local"

        todo = Todo()
        todo.add("uid", uid)
        todo.add("summary", content)
        todo.add("dtstamp", now)
        todo.add("status", "COMPLETED" if done else "NEEDS-ACTION")
        todo.add("percent-complete", 100 if done else 0)
        if done:
            todo.add("completed", now)

        # Add to merged calendar
        merged.add_component(todo)

        # Upload this VTODO as its own resource to Radicale (PUT)
        single = Calendar()
        single.add("prodid", "-//todo.json->CalDAV//EN")
        single.add("version", "2.0")
        single.add_component(todo)

        ics_bytes = single.to_ical()
        put_url = f"{calendar_url}{uid}.ics"
        resp = requests.put(
            put_url,
            data=ics_bytes,
            auth=(username, password),
            headers={"Content-Type": "text/calendar; charset=utf-8"},
            verify=verify_ssl,
            timeout=30,
        )
        # Raise if server rejects it (4xx/5xx)
        resp.raise_for_status()
        uploaded.append(put_url)

    if output_ics_path:
        with open(output_ics_path, "wb") as f:
            f.write(merged.to_ical())

    return uploaded

if __name__ == "__main__":

    CALENDAR_URL = os.getenv("CALDAV_URL")
    USERNAME = os.getenv("CALDAV_USERNAME")
    PASSWORD = os.getenv("CALDAV_PASSWORD")
    uploaded_urls = sync_todos_json_to_caldav(
        json_path="todo.json",
        calendar_url=CALENDAR_URL,
        username=USERNAME,
        password=PASSWORD,
        output_ics_path="todos-export.ics",  # optional
        verify_ssl=True,                     # set False only if you know what you're doing
    )

    print("\n".join(uploaded_urls))
