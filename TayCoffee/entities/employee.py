"""
Entity: Employee (NhanVien) — Base class + ThuNgan, QuanLy
Tuân thủ LSP: Các lớp con không thay đổi hành vi kỳ vọng của lớp cha.
"""
from __future__ import annotations
from typing import Optional


class Employee:
    """NhanVien — Lớp cha cho tất cả nhân viên."""

    BASE_SALARY_PER_HOUR = 30_000  # VNĐ

    def __init__(self, employee_id: str, full_name: str, position: str,
                 phone: str = '', address: str = ''):
        self._employee_id = employee_id
        self._full_name = full_name
        self._position = position
        self._phone = phone
        self._address = address

    # ---------- Properties (getter/setter) ----------
    @property
    def employee_id(self) -> str:
        return self._employee_id

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str):
        self._full_name = value

    @property
    def position(self) -> str:
        return self._position

    @position.setter
    def position(self, value: str):
        self._position = value

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str):
        self._phone = value

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str):
        self._address = value

    # ---------- Methods ----------
    def calculate_salary(self) -> float:
        """tinhLuong() — lớp con sẽ override."""
        return 0.0

    def create_order(self):
        """taoDonHang() — placeholder, controller xử lý logic thực."""
        pass

    def create_import_receipt(self):
        """lapPhieuNhap() — placeholder."""
        pass

    # ---------- Serialization ----------
    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Employee']:
        if not row:
            return None
        return cls(
            employee_id=str(row.get('userid', '')),
            full_name=row.get('fullname', ''),
            position=row.get('roleid', ''),
            phone=row.get('phone', ''),
            address=''
        )

    def to_dict(self) -> dict:
        return {
            'employee_id': self._employee_id,
            'full_name': self._full_name,
            'position': self._position,
            'phone': self._phone,
            'address': self._address,
        }


class Cashier(Employee):
    """ThuNgan — Nhân viên thu ngân (extends Employee).
    Override tinhLuong = luongCB * soGio.
    """

    def __init__(self, employee_id: str, full_name: str, phone: str = '',
                 address: str = '', hours_worked: int = 0):
        super().__init__(employee_id, full_name, 'Cashier', phone, address)
        self._hours_worked = hours_worked

    @property
    def hours_worked(self) -> int:
        return self._hours_worked

    @hours_worked.setter
    def hours_worked(self, value: int):
        self._hours_worked = max(0, value)

    def calculate_salary(self) -> float:
        """luongCB * soGio"""
        return self.BASE_SALARY_PER_HOUR * self._hours_worked


class Manager(Employee):
    """QuanLy — Quản lý (extends Employee).
    Override tinhLuong = luongCB + phuCap.
    """

    DEFAULT_BASE = 15_000_000  # Lương cơ bản cố định / tháng

    def __init__(self, employee_id: str, full_name: str, phone: str = '',
                 address: str = '', allowance: float = 0.0):
        super().__init__(employee_id, full_name, 'Manager', phone, address)
        self._allowance = allowance

    @property
    def allowance(self) -> float:
        return self._allowance

    @allowance.setter
    def allowance(self, value: float):
        self._allowance = max(0.0, value)

    def calculate_salary(self) -> float:
        """luongCB + phuCap"""
        return self.DEFAULT_BASE + self._allowance
