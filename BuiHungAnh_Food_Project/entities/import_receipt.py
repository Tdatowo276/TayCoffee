"""
Entity: ImportReceipt (PhieuNhap) — Phiếu nhập kho.
"""
from __future__ import annotations
from datetime import date
from typing import List, Optional


class ImportReceiptItem:
    """Chi tiết một dòng trong phiếu nhập."""

    def __init__(self, ingredient_id: str, quantity: float, unit_price: float):
        self._ingredient_id = ingredient_id
        self._quantity = quantity
        self._unit_price = unit_price

    @property
    def ingredient_id(self) -> str:
        return self._ingredient_id

    @property
    def quantity(self) -> float:
        return self._quantity

    @property
    def unit_price(self) -> float:
        return self._unit_price

    @property
    def subtotal(self) -> float:
        return self._quantity * self._unit_price

    def to_dict(self) -> dict:
        return {
            'ingredient_id': self._ingredient_id,
            'quantity': self._quantity,
            'unit_price': self._unit_price,
            'subtotal': self.subtotal,
        }


class ImportReceipt:
    """PhieuNhap — Phiếu nhập kho nguyên liệu."""

    def __init__(self, receipt_id: str, import_date: Optional[date] = None,
                 total: float = 0.0, supplier: str = ''):
        self._receipt_id = receipt_id
        self._import_date = import_date or date.today()
        self._total = total
        self._supplier = supplier
        self._items: List[ImportReceiptItem] = []

    # ---------- Properties ----------
    @property
    def receipt_id(self) -> str:
        return self._receipt_id

    @property
    def import_date(self) -> date:
        return self._import_date

    @property
    def total(self) -> float:
        return self._total

    @property
    def supplier(self) -> str:
        return self._supplier

    @supplier.setter
    def supplier(self, value: str):
        self._supplier = value

    @property
    def items(self) -> List[ImportReceiptItem]:
        return self._items

    # ---------- Methods ----------
    def add_item(self, ingredient_id: str, quantity: float, unit_price: float):
        item = ImportReceiptItem(ingredient_id, quantity, unit_price)
        self._items.append(item)
        self._total = self.calculate_total()

    def calculate_total(self) -> float:
        """tinhTongTien() — Tính tổng tiền phiếu nhập."""
        self._total = sum(i.subtotal for i in self._items)
        return self._total

    # ---------- Serialization ----------
    def to_dict(self) -> dict:
        return {
            'receipt_id': self._receipt_id,
            'import_date': self._import_date.isoformat(),
            'total': self._total,
            'supplier': self._supplier,
            'items': [i.to_dict() for i in self._items],
        }
