import json
from typing import Iterable, List
from ..domain import Todo

class JsonTodoStore:
    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> List[Todo]:
        with open(self.path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        out: List[Todo] = []
        for it in raw:
            # minimal fields required; others optional
            out.append(Todo(
                uid=it.get("uid") or "",
                content=(it.get("content") or "").strip(),
                done=bool(it.get("done", False)),
                status=it.get("status") or ("COMPLETED" if it.get("done") else "NEEDS-ACTION"),
                percent_complete=int(it.get("percent_complete", 100 if it.get("done") else 0)),
                dtstamp=None, created=None, last_modified=None, completed=None, due=None,
                description=it.get("description"), priority=it.get("priority"),
                categories=it.get("categories"),
            ))
        return out

    def save(self, todos: Iterable[Todo]) -> None:
        def _ser(t: Todo):
            return {
                "uid": t.uid,
                "content": t.content,
                "done": bool(t.done),
                "status": t.status,
                "percent_complete": t.percent_complete,
                "dtstamp": t.dtstamp.isoformat().replace("+00:00", "Z") if t.dtstamp else None,
                "created": t.created.isoformat().replace("+00:00", "Z") if t.created else None,
                "last_modified": t.last_modified.isoformat().replace("+00:00", "Z") if t.last_modified else None,
                "completed": t.completed.isoformat().replace("+00:00", "Z") if t.completed else None,
                "due": (t.due.isoformat() if t.due else None),
                "description": t.description,
                "priority": t.priority,
                "categories": t.categories,
            }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([_ser(t) for t in todos], f, ensure_ascii=False, indent=2)
