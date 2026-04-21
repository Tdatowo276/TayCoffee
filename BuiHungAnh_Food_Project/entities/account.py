"""
Entity: Account (TaiKhoan) — Quản lý tài khoản đăng nhập.
"""
from __future__ import annotations
import hashlib
from typing import Optional


class Account:
    """TaiKhoan — Tài khoản đăng nhập hệ thống."""

    def __init__(self, username: str, password_hash: str,
                 access_role: str = 'staff', status: str = 'active'):
        self._username = username
        self._password_hash = password_hash
        self._access_role = access_role
        self._status = status

    # ---------- Properties ----------
    @property
    def username(self) -> str:
        return self._username

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def access_role(self) -> str:
        return self._access_role

    @access_role.setter
    def access_role(self, value: str):
        self._access_role = value

    @property
    def status(self) -> str:
        return self._status

    # ---------- Methods ----------
    def login(self, plain_password: str) -> bool:
        """dangNhap() — Xác thực mật khẩu."""
        input_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return input_hash == self._password_hash

    def logout(self):
        """dangXuat()"""
        self._status = 'logged_out'

    def authenticate(self) -> bool:
        """xacThuc() — Kiểm tra tài khoản có đang hoạt động."""
        return self._status == 'active'

    def lock_account(self):
        """khoaTaiKhoan()"""
        self._status = 'locked'

    # ---------- Helpers ----------
    @staticmethod
    def hash_password(plain_password: str) -> str:
        return hashlib.sha256(plain_password.encode('utf-8')).hexdigest()

    @classmethod
    def from_db_row(cls, row: dict) -> Optional['Account']:
        if not row:
            return None
        return cls(
            username=row.get('email', ''),
            password_hash=row.get('passwordhash', ''),
            access_role=str(row.get('roleid', 3)),
            status='active' if row.get('isactive', True) else 'locked'
        )

    def to_dict(self) -> dict:
        return {
            'username': self._username,
            'access_role': self._access_role,
            'status': self._status,
        }
