"""
Entity: Invoice (HoaDon) — Hóa đơn thanh toán.
Implements TinhTien interface.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional


class Invoice:
    """HoaDon — Hóa đơn thanh toán."""

    def __init__(self, invoice_id: str, payment_date: Optional[datetime] = None,
                 total: float = 0.0, payment_method: str = 'Cash',
                 discount: float = 0.0):
        self._invoice_id = invoice_id
        self._payment_date = payment_date
        self._total = total
        self._payment_method = payment_method
        self._discount = discount

    # ---------- Properties ----------
    @property
    def invoice_id(self) -> str:
        return self._invoice_id

    @property
    def payment_date(self) -> Optional[datetime]:
        return self._payment_date

    @property
    def total(self) -> float:
        return self._total

    @property
    def payment_method(self) -> str:
        return self._payment_method

    @payment_method.setter
    def payment_method(self, value: str):
        self._payment_method = value

    @property
    def discount(self) -> float:
        return self._discount

    @discount.setter
    def discount(self, value: float):
        self._discount = max(0.0, value)

    # ---------- Methods ----------
    def calculate_final(self) -> float:
        """tinhTienCuoi() — Tính tiền cuối cùng sau giảm giá."""
        final = self._total - self._discount
        return max(0.0, final)

    def process_payment(self) -> bool:
        """thanhToan() — Xử lý thanh toán."""
        self._payment_date = datetime.now()
        return True

    def calculate_amount(self) -> float:
        """tinhTien() — TinhTien interface implementation."""
        return self.calculate_final()

    # ---------- Serialization ----------
    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Invoice']:
        if not row:
            return None
        return cls(
            invoice_id=str(row.get('paymentid', '')),
            payment_date=row.get('paidat'),
            total=float(row.get('amount', 0)),
            payment_method=row.get('method', 'Cash'),
            discount=0.0
        )

    def to_dict(self) -> dict:
        return {
            'invoice_id': self._invoice_id,
            'payment_date': self._payment_date.isoformat() if self._payment_date else None,
            'total': self._total,
            'payment_method': self._payment_method,
            'discount': self._discount,
            'final_amount': self.calculate_final(),
        }
