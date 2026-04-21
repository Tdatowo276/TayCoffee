"""
Interfaces Nghiệp Vụ (Business Contracts) — ISP compliance.
Mỗi interface chuyên biệt cho một nhóm chức năng.
"""
from abc import ABC, abstractmethod
from typing import List
from datetime import date


class IOrderService(ABC):
    """IGoiMon — Interface gọi món."""

    @abstractmethod
    def create_order(self, table_id: str):
        """taoDonHang(ban) -> DonHang"""
        pass

    @abstractmethod
    def add_item(self, order_id: str, product_id: str,
                 quantity: int, note: str = ''):
        """themMon(don, sp, sl, gc)"""
        pass

    @abstractmethod
    def remove_item(self, order_id: str, product_id: str):
        """xoaMon(don, sp)"""
        pass


class IPaymentService(ABC):
    """IThanhToan — Interface thanh toán."""

    @abstractmethod
    def process_payment(self, order_id: str, payment_method):
        """thanhToan(don, pt) -> HoaDon"""
        pass

    @abstractmethod
    def apply_discount(self, order_id: str, promo_code: str):
        """apDungGiamGia(don, ma)"""
        pass

    @abstractmethod
    def print_invoice(self, invoice_id: str) -> dict:
        """inHoaDon(hd)"""
        pass


class IInventoryService(ABC):
    """IQuanLyKho — Interface quản lý kho."""

    @abstractmethod
    def import_stock(self, receipt) -> bool:
        """nhapKho(phieu)"""
        pass

    @abstractmethod
    def check_inventory(self) -> list:
        """kiemTraTonKho() -> List<NguyenLieu>"""
        pass

    @abstractmethod
    def get_low_stock_alerts(self) -> list:
        """canhBao() -> List<NguyenLieu>"""
        pass


class IEmployeeService(ABC):
    """IQuanLyNhanVien — Interface quản lý nhân viên."""

    @abstractmethod
    def add_employee(self, employee) -> bool:
        """themNV(nv)"""
        pass

    @abstractmethod
    def update_employee(self, employee) -> bool:
        """suaNV(nv)"""
        pass

    @abstractmethod
    def remove_employee(self, employee_id: str) -> bool:
        """xoaNV(maNV)"""
        pass


class IReportService(ABC):
    """IBaoCao — Interface báo cáo."""

    @abstractmethod
    def generate_report(self, from_date: date, to_date: date) -> dict:
        """taoBaoCao(tuNgay, denNgay) -> Result"""
        pass

    @abstractmethod
    def report_name(self) -> str:
        """tenBaoCao()"""
        pass
