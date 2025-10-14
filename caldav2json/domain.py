
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Literal

TodoStatus = Literal["NEEDS-ACTION", "COMPLETED"]

@dataclass(frozen=True)
class Todo:
    uid: str                      # stable deterministic id
    content: str                  # SUMMARY
    done: bool
    status: TodoStatus
    percent_complete: int
    dtstamp: Optional[datetime]   # UTC, seconds precision
    created: Optional[datetime]
    last_modified: Optional[datetime]
    completed: Optional[datetime]
    due: Optional[datetime | date]
    description: Optional[str]
    priority: Optional[int]
    categories: Optional[List[str]]

    @staticmethod
    def canonical_status(done: bool, status: Optional[str], pct: Optional[int]) -> tuple[TodoStatus, int, bool]:
        is_done = done or (pct == 100) or (status or "").upper() == "COMPLETED"
        pc = 100 if is_done else (0 if pct is None else pct)
        st: TodoStatus = "COMPLETED" if is_done else "NEEDS-ACTION"
        return st, pc, is_done
