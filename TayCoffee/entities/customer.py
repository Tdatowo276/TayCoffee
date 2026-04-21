"""
Entity: Customer (KhachHang) — Khách hàng với điểm tích lũy.
"""
from __future__ import annotations
from typing import Optional


class Customer:
    """KhachHang — Khách hàng."""

    def __init__(self, customer_id: str, name: str,
                 phone: str = '', loyalty_points: int = 0):
        self._customer_id = customer_id
        self._name = name
        self._phone = phone
        self._loyalty_points = loyalty_points

    # ---------- Properties ----------
    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str):
        self._phone = value

    @property
    def loyalty_points(self) -> int:
        return self._loyalty_points

    # ---------- Methods ----------
    def add_points(self, points: int):
        """congDiem() — Cộng điểm tích lũy."""
        self._loyalty_points += max(0, points)

    def deduct_points(self, points: int) -> bool:
        """truDiem() — Trừ điểm tích lũy."""
        if points > self._loyalty_points:
            return False
        self._loyalty_points -= points
        return True

    # ---------- Serialization ----------
    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Customer']:
        if not row:
            return None
        return cls(
            customer_id=str(row.get('userid', '')),
            name=row.get('fullname', ''),
            phone=row.get('phone', ''),
            loyalty_points=0
        )

    def to_dict(self) -> dict:
        return {
            'customer_id': self._customer_id,
            'name': self._name,
            'phone': self._phone,
            'loyalty_points': self._loyalty_points,
        }
