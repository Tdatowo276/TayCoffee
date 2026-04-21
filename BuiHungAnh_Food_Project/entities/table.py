"""
Entity: Table (Ban) — Quản lý bàn trong quán.
"""
from __future__ import annotations
from typing import Optional


class Table:
    """Ban — Bàn phục vụ khách."""

    VALID_STATUSES = ('Empty', 'Occupied', 'Reserved')

    def __init__(self, table_id: str, table_name: str,
                 status: str = 'Empty', location: str = ''):
        self._table_id = table_id
        self._table_name = table_name
        self._status = status if status in self.VALID_STATUSES else 'Empty'
        self._location = location

    # ---------- Properties ----------
    @property
    def table_id(self) -> str:
        return self._table_id

    @property
    def table_name(self) -> str:
        return self._table_name

    @table_name.setter
    def table_name(self, value: str):
        self._table_name = value

    @property
    def status(self) -> str:
        return self._status

    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, value: str):
        self._location = value

    # ---------- Methods ----------
    def update_status(self, new_status: str) -> bool:
        """capNhatTrangThai() — Cập nhật trạng thái bàn."""
        if new_status not in self.VALID_STATUSES:
            return False
        self._status = new_status
        return True

    # ---------- Serialization ----------
    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Table']:
        if not row:
            return None
        return cls(
            table_id=str(row.get('tableid', '')),
            table_name=row.get('tablenumber', ''),
            status=row.get('status', 'Empty'),
            location=''
        )

    def to_dict(self) -> dict:
        return {
            'table_id': self._table_id,
            'table_name': self._table_name,
            'status': self._status,
            'location': self._location,
        }
