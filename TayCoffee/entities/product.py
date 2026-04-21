"""
Entity: Product (SanPham) — Sản phẩm trong menu.
"""
from __future__ import annotations
from typing import Optional


class Product:
    """SanPham — Sản phẩm / món trong menu quán."""

    def __init__(self, product_id: str, name: str, price: float,
                 category: str = '', status: str = 'active',
                 image: str = '☕', description: str = ''):
        self._product_id = product_id
        self._name = name
        self._price = price
        self._category = category
        self._status = status
        self._image = image
        self._description = description

    # ---------- Properties ----------
    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def price(self) -> float:
        return self._price

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, value: str):
        self._category = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        self._status = value

    @property
    def image(self) -> str:
        return self._image

    @image.setter
    def image(self, value: str):
        self._image = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value

    # ---------- Methods ----------
    def update_price(self, new_price: float) -> bool:
        """capNhatGia() — Cập nhật giá sản phẩm."""
        if new_price < 0:
            return False
        self._price = new_price
        return True

    # ---------- Serialization ----------
    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Product']:
        if not row:
            return None
        return cls(
            product_id=str(row.get('productid', '')),
            name=row.get('productname', ''),
            price=float(row.get('price', 0)),
            category=str(row.get('categoryid', '')),
            status='active' if row.get('isactive', True) else 'inactive',
            image=row.get('imageurl', '☕'),
            description=row.get('description', '')
        )

    def to_dict(self) -> dict:
        return {
            'product_id': self._product_id,
            'name': self._name,
            'price': self._price,
            'category': self._category,
            'status': self._status,
            'image': self._image,
            'description': self._description,
        }
