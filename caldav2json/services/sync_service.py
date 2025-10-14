
import hashlib
from datetime import datetime, timezone
from ..domain import Todo
from ..ports import TodoStore, CalendarStore, TodoCodec

class SyncService:
    def __init__(self, json_store: TodoStore, cal_store: CalendarStore, codec: TodoCodec):
        self.json_store = json_store
        self.cal_store = cal_store
        self.codec = codec

    @staticmethod
    def make_uid(content: str) -> str:
        return "todo-" + hashlib.sha1(content.encode("utf-8")).hexdigest() + "@local"

    def upsync_json_to_caldav(self) -> list[str]:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        uploaded: list[str] = []
        todos = []
        for item in self.json_store.load():
            content = (item.content or "").strip()
            if not content:
                continue
            uid = item.uid or self.make_uid(content)
            st, pc, done = Todo.canonical_status(item.done, item.status, item.percent_complete)
            todos.append(Todo(
                uid=uid,
                content=content,
                done=done,
                status=st,
                percent_complete=pc,
                dtstamp=now,
                created=item.created,
                last_modified=item.last_modified,
                completed=(now if done and not item.completed else item.completed),
                due=item.due,
                description=item.description,
                priority=item.priority,
                categories=item.categories,
            ))

        # Upload one-by-one as separate resources
        for t in todos:
            ics = self.codec.to_ics([t])
            url = self.cal_store.put_vtodo(ics, t.uid)
            uploaded.append(url)
        return uploaded
