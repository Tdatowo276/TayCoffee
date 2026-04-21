"""
Entity: Shift (CaLam) — Ca làm việc của nhân viên.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional


class Shift:
    """CaLam — Quản lý ca làm việc."""

    def __init__(self, shift_id: str, start_time: datetime,
                 end_time: Optional[datetime] = None,
                 work_date: Optional[datetime] = None):
        self._shift_id = shift_id
        self._start_time = start_time
        self._end_time = end_time
        self._work_date = work_date or start_time

    # ---------- Properties ----------
    @property
    def shift_id(self) -> str:
        return self._shift_id

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @start_time.setter
    def start_time(self, value: datetime):
        self._start_time = value

    @property
    def end_time(self) -> Optional[datetime]:
        return self._end_time

    @end_time.setter
    def end_time(self, value: Optional[datetime]):
        self._end_time = value

    @property
    def work_date(self) -> datetime:
        return self._work_date

    # ---------- Methods ----------
    def calculate_hours(self) -> float:
        """tinhSoGioLam() — Tính tổng số giờ làm."""
        if not self._end_time:
            return 0.0
        delta = self._end_time - self._start_time
        return round(delta.total_seconds() / 3600, 2)

    # ---------- Serialization ----------
    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Shift']:
        if not row:
            return None
        return cls(
            shift_id=str(row.get('shiftid', '')),
            start_time=row.get('starttime', datetime.now()),
            end_time=row.get('endtime'),
            work_date=row.get('starttime')
        )

    def to_dict(self) -> dict:
        return {
            'shift_id': self._shift_id,
            'start_time': self._start_time.isoformat() if self._start_time else None,
            'end_time': self._end_time.isoformat() if self._end_time else None,
            'hours': self.calculate_hours(),
        }
