
from ..ports import CalendarStore, TodoCodec

class ExportService:
    def __init__(self, cal_store: CalendarStore, codec: TodoCodec):
        self.cal = cal_store
        self.codec = codec

    def merged_ics(self) -> bytes:
        ics_blobs = self.cal.list_objects() + self.cal.list_todos()
        todos = []
        for blob in ics_blobs:
            try:
                todos.extend(self.codec.from_ics(blob))
            except Exception:
                continue
        return self.codec.to_ics(todos)
