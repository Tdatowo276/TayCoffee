"""
Entity: Ingredient (NguyenLieu) — Nguyên liệu kho.
"""
from __future__ import annotations
from typing import Optional


class Ingredient:
    """NguyenLieu — Nguyên liệu trong kho."""

    def __init__(self, ingredient_id: str, name: str,
                 quantity: float = 0.0, unit: str = 'g',
                 min_threshold: float = 100.0):
        self._ingredient_id = ingredient_id
        self._name = name
        self._quantity = quantity
        self._unit = unit
        self._min_threshold = min_threshold

    # ---------- Properties ----------
    @property
    def ingredient_id(self) -> str:
        return self._ingredient_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def quantity(self) -> float:
        return self._quantity

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def min_threshold(self) -> float:
        return self._min_threshold

    @min_threshold.setter
    def min_threshold(self, value: float):
        self._min_threshold = max(0.0, value)

    # ---------- Methods ----------
    def update_quantity(self, delta: float):
        """capNhatSoLuong() — Cập nhật số lượng (cộng hoặc trừ)."""
        self._quantity += delta
        if self._quantity < 0:
            self._quantity = 0

    def is_low_stock(self) -> bool:
        """Kiểm tra tồn kho có dưới mức tối thiểu."""
        return self._quantity < self._min_threshold

    # ---------- Serialization ----------
    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Ingredient']:
        if not row:
            return None
        return cls(
            ingredient_id=str(row.get('ingredientid', '')),
            name=row.get('ingredientname', ''),
            quantity=float(row.get('stockamount', 0)),
            unit=row.get('unit', 'g'),
            min_threshold=float(row.get('minstockthreshold', 100))
        )

    def to_dict(self) -> dict:
        return {
            'ingredient_id': self._ingredient_id,
            'name': self._name,
            'quantity': self._quantity,
            'unit': self._unit,
            'min_threshold': self._min_threshold,
            'is_low_stock': self.is_low_stock(),
        }
