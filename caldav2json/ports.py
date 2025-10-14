
# ports.py
from typing import Iterable, Protocol, List, Optional
from .domain import Todo

class TodoCodec(Protocol):
    def to_ics(self, todos: Iterable[Todo]) -> bytes: ...
    def from_ics(self, ics_bytes: bytes) -> List[Todo]: ...

class TodoStore(Protocol):
    def load(self) -> List[Todo]: ...
    def save(self, todos: Iterable[Todo]) -> None: ...

class CalendarStore(Protocol):
    def list_objects(self) -> List[bytes]: ...         # raw ICS payloads
    def list_todos(self) -> List[bytes]: ...
    def put_vtodo(self, todo_ics: bytes, uid: str) -> str: ...  # returns URL
