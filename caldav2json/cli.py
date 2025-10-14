
import sys, argparse, pathlib
from caldav2json.config import load_settings
from caldav2json.adapters.ics_codec import IcsCodec
from caldav2json.adapters.json_store import JsonTodoStore
from caldav2json.adapters.caldav_store import RadicaleCalendarStore
from caldav2json.services.export_service import ExportService
from caldav2json.services.sync_service import SyncService

def main(argv=None):
    p = argparse.ArgumentParser(prog="radatodo")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("export", help="Export merged ICS from Radicale")
    e.add_argument("--out", default="calendar-export.ics")

    s = sub.add_parser("sync", help="Sync JSON todos -> Radicale")
    s.add_argument("--json", default="todo.json")

    j = sub.add_parser("dump-json", help="Dump VTODOs from Radicale as JSON")
    j.add_argument("--out", default="todos.json")

    args = p.parse_args(argv)
    cfg = load_settings()
    codec = IcsCodec()
    cal = RadicaleCalendarStore(cfg.caldav_url, cfg.username, cfg.password, cfg.verify_ssl)

    if args.cmd == "export":
        out = ExportService(cal, codec).merged_ics()
        pathlib.Path(args.out).write_bytes(out)
        return 0

    if args.cmd == "sync":
        store = JsonTodoStore(args.json)
        uploaded = SyncService(store, cal, codec).upsync_json_to_caldav()
        print("\n".join(uploaded))
        return 0

    if args.cmd == "dump-json":
        # Radicale -> ICS -> Todo -> JSON
        ics_blobs = cal.list_todos()
        todos = []
        for b in ics_blobs:
            todos.extend(codec.from_ics(b))
        JsonTodoStore(args.out).save(todos)
        return 0

    return 1

if __name__ == "__main__":
    raise SystemExit(main())
