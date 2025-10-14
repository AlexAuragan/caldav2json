from caldav import DAVClient, Calendar
from icalendar import Calendar as ICalendar
import os

CALENDAR_URL = os.getenv("CALDAV_URL")
assert CALENDAR_URL
USERNAME = os.getenv("CALDAV_USERNAME")
PASSWORD = os.getenv("CALDAV_PASSWORD")
OUTPUT_ICS = "calendar-export.ics"

def export_calendar(caldav_calendar, out_path: str) -> None:
    merged = ICalendar()
    merged.add("prodid", "-//Radicale Export//EN")
    merged.add("version", "2.0")

    # 1) Generic objects (often VEVENTs; may include VTODOs on some servers)
    for obj in caldav_calendar.objects():
        try:
            data = obj.data
            if data is None:
                try:
                    data = obj._get_data()
                except Exception:
                    data = None
            if data is None:
                continue

            if isinstance(data, bytes):
                try:
                    data = data.decode("utf-8")
                except Exception:
                    data = data.decode("latin-1", errors="replace")

            cal = ICalendar.from_ical(data)
            for comp in cal.walk():
                if comp.name in ("VTIMEZONE", "VEVENT", "VTODO"):
                    merged.add_component(comp)
        except Exception:
            continue

    # 2) Explicitly fetch VTODOs (needed when objects() doesn't include them)
    try:
        todos_iter = caldav_calendar.todos()
    except Exception:
        todos_iter = []

    for obj in todos_iter:
        try:
            data = obj.data
            if data is None:
                try:
                    data = obj._get_data()
                except Exception:
                    data = None
            if data is None:
                continue

            if isinstance(data, bytes):
                try:
                    data = data.decode("utf-8")
                except Exception:
                    data = data.decode("latin-1", errors="replace")

            cal = ICalendar.from_ical(data)
            for comp in cal.walk():
                if comp.name in ("VTIMEZONE", "VEVENT", "VTODO"):
                    merged.add_component(comp)
        except Exception:
            continue

    with open(out_path, "wb") as f:
        f.write(merged.to_ical())


def main():
    client = DAVClient(url=CALENDAR_URL, username=USERNAME, password=PASSWORD)
    cal = Calendar(client=client, url=CALENDAR_URL)
    export_calendar(cal, OUTPUT_ICS)

if __name__ == "__main__":
    main()
