"""
Entity: Order (DonHang) + OrderDetail (ChiTietDonHang)
DonHang implements TinhTien interface.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional


class OrderDetail:
    """ChiTietDonHang — Một dòng chi tiết trong đơn hàng."""

    def __init__(self, product_id: str, quantity: int,
                 unit_price: float, note: str = ''):
        self._product_id = product_id
        self._quantity = quantity
        self._unit_price = unit_price
        self._subtotal = unit_price * quantity
        self._note = note

    # ---------- Properties ----------
    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int):
        self._quantity = max(1, value)
        self._subtotal = self._unit_price * self._quantity

    @property
    def unit_price(self) -> float:
        return self._unit_price

    @property
    def subtotal(self) -> float:
        return self._subtotal

    @property
    def note(self) -> str:
        return self._note

    @note.setter
    def note(self, value: str):
        self._note = value

    # ---------- Methods ----------
    def calculate_subtotal(self) -> float:
        """tinhThanhTien()"""
        self._subtotal = self._unit_price * self._quantity
        return self._subtotal

    def to_dict(self) -> dict:
        return {
            'product_id': self._product_id,
            'quantity': self._quantity,
            'unit_price': self._unit_price,
            'subtotal': self._subtotal,
            'note': self._note,
        }


class Order:
    """DonHang — Đơn hàng (implements TinhTien)."""

    VALID_STATUSES = ('pending', 'processing', 'completed', 'cancelled')

    def __init__(self, order_id: str, created_at: Optional[datetime] = None,
                 total: float = 0.0, status: str = 'pending', notes: str = ''):
        self._order_id = order_id
        self._created_at = created_at or datetime.now()
        self._total = total
        self._status = status
        self._notes = notes
        self._items: List[OrderDetail] = []

    # ---------- Properties ----------
    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def total(self) -> float:
        return self._total

    @property
    def status(self) -> str:
        return self._status

    @property
    def notes(self) -> str:
        return self._notes

    @notes.setter
    def notes(self, value: str):
        self._notes = value

    @property
    def items(self) -> List[OrderDetail]:
        return self._items

    # ---------- Methods ----------
    def add_product(self, product_id: str, quantity: int,
                    unit_price: float, note: str = ''):
        """themSanPham() — Thêm sản phẩm vào đơn hàng."""
        detail = OrderDetail(product_id, quantity, unit_price, note)
        self._items.append(detail)
        self._recalculate_total()

    def remove_product(self, product_id: str):
        """Xóa sản phẩm khỏi đơn hàng."""
        self._items = [i for i in self._items if i.product_id != product_id]
        self._recalculate_total()

    def calculate_total(self) -> float:
        """tinhTongTien() — Tính tổng tiền đơn hàng."""
        return self._recalculate_total()

    def calculate_amount(self) -> float:
        """tinhTien() — Interface TinhTien implementation."""
        return self._total

    def update_status(self, new_status: str) -> bool:
        """capNhatTrangThai()"""
        if new_status not in self.VALID_STATUSES:
            return False
        self._status = new_status
        return True

    def _recalculate_total(self) -> float:
        self._total = sum(item.subtotal for item in self._items)
        return self._total

    # ---------- Serialization ----------
    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Order']:
        if not row:
            return None
        return cls(
            order_id=str(row.get('orderid', '')),
            created_at=row.get('orderdate'),
            total=float(row.get('totalamount', 0) or row.get('subtotal', 0)),
            status=row.get('orderstatus', 'pending'),
            notes=row.get('notes', '')
        )

    def to_dict(self) -> dict:
        return {
            'order_id': self._order_id,
            'created_at': self._created_at.isoformat() if self._created_at else None,
            'total': self._total,
            'status': self._status,
            'notes': self._notes,
            'items': [i.to_dict() for i in self._items],
        }
