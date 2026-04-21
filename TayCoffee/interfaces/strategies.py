"""
Strategy Interfaces + Implementations — OCP & DIP compliance.
KHÔNG dùng if-else để phân loại. Dùng đa hình (polymorphism).
"""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List

from models.db_client import execute_query


# ============================================================
# Interface: Calculable (TinhTien)
# ============================================================
class Calculable(ABC):
    """<<interface>> TinhTien — Tính tiền."""

    @abstractmethod
    def calculate_amount(self) -> float:
        """tinhTien()"""
        pass


# ============================================================
# Interface: PaymentMethod (PhuongThucThanhToan)
# ============================================================
class PaymentMethod(ABC):
    """PhuongThucThanhToan — Strategy cho phương thức thanh toán.
    KHÔNG dùng if-else / switch-case. Mỗi phương thức = 1 class.
    """

    @abstractmethod
    def pay(self, total: float) -> float:
        """thanhToan(tongTien) -> số tiền đã thanh toán"""
        pass

    @abstractmethod
    def method_name(self) -> str:
        """tenPhuongThuc()"""
        pass


class CashPayment(PaymentMethod):
    """TienMat — Thanh toán bằng tiền mặt."""

    def pay(self, total: float) -> float:
        return total

    def method_name(self) -> str:
        return 'Cash'


class MoMoPayment(PaymentMethod):
    """MoMo — Thanh toán qua ví MoMo."""

    def pay(self, total: float) -> float:
        # Có thể thêm phí dịch vụ nếu cần
        return total

    def method_name(self) -> str:
        return 'QR'


class BankTransferPayment(PaymentMethod):
    """ChuyenKhoan — Thanh toán chuyển khoản ngân hàng."""

    def pay(self, total: float) -> float:
        return total

    def method_name(self) -> str:
        return 'BankTransfer'


class CardPayment(PaymentMethod):
    """Thẻ — Thanh toán bằng thẻ."""

    def pay(self, total: float) -> float:
        return total

    def method_name(self) -> str:
        return 'Card'


# Factory — Tạo PaymentMethod từ tên (thay thế if-else ở Controller)
PAYMENT_REGISTRY = {
    'Cash': CashPayment,
    'QR': MoMoPayment,
    'BankTransfer': BankTransferPayment,
    'Card': CardPayment,
}


def get_payment_method(method_name: str) -> PaymentMethod:
    """Factory function — DIP compliant, không cần if-else."""
    cls = PAYMENT_REGISTRY.get(method_name, CashPayment)
    return cls()


# ============================================================
# Interface: ReportStrategy (BaoCaoStrategy)
# ============================================================
class ReportStrategy(ABC):
    """BaoCaoStrategy — Strategy cho các loại báo cáo.
    KHÔNG dùng if-else để phân loại. Mỗi loại = 1 class.
    """

    @abstractmethod
    def generate(self, from_date: date, to_date: date) -> dict:
        """taoBaoCao(tuNgay, denNgay) -> Result"""
        pass

    @abstractmethod
    def report_name(self) -> str:
        """tenBaoCao()"""
        pass


class RevenueReport(ReportStrategy):
    """BaoCaoDoanhThu — Báo cáo doanh thu."""

    def generate(self, from_date: date, to_date: date) -> dict:
        sql = """
            SELECT DATE(orderdate) as day, 
                   SUM(subtotal - discount) as revenue,
                   COUNT(*) as order_count
            FROM Orders
            WHERE orderdate >= %s AND orderdate < %s
              AND orderstatus != 'cancelled'
            GROUP BY DATE(orderdate)
            ORDER BY day
        """
        rows = execute_query(sql, [
            datetime.combine(from_date, datetime.min.time()),
            datetime.combine(to_date, datetime.max.time())
        ], fetch=True)

        total_revenue = sum(float(r.get('revenue', 0)) for r in rows)
        total_orders = sum(int(r.get('order_count', 0)) for r in rows)

        return {
            'report_name': self.report_name(),
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'daily': [{
                'date': str(r.get('day', '')),
                'revenue': float(r.get('revenue', 0)),
                'orders': int(r.get('order_count', 0))
            } for r in rows]
        }

    def report_name(self) -> str:
        return 'Báo cáo Doanh thu'


class BestSellerReport(ReportStrategy):
    """BaoCaoMonBanChay — Báo cáo món bán chạy."""

    def generate(self, from_date: date, to_date: date) -> dict:
        sql = """
            SELECT p.productname, p.imageurl,
                   SUM(od.quantity) as total_sold,
                   SUM(od.quantity * od.unitprice) as revenue
            FROM OrderDetails od
            JOIN Products p ON od.productid = p.productid
            JOIN Orders o ON od.orderid = o.orderid
            WHERE o.orderdate >= %s AND o.orderdate < %s
              AND o.orderstatus != 'cancelled'
            GROUP BY p.productid, p.productname, p.imageurl
            ORDER BY total_sold DESC
            LIMIT 10
        """
        rows = execute_query(sql, [
            datetime.combine(from_date, datetime.min.time()),
            datetime.combine(to_date, datetime.max.time())
        ], fetch=True)

        return {
            'report_name': self.report_name(),
            'from_date': from_date.isoformat(),
            'to_date': to_date.isoformat(),
            'items': [{
                'name': r.get('productname', ''),
                'image': r.get('imageurl', '☕'),
                'total_sold': int(r.get('total_sold', 0)),
                'revenue': float(r.get('revenue', 0))
            } for r in rows]
        }

    def report_name(self) -> str:
        return 'Báo cáo Món bán chạy'


# Factory — Tạo ReportStrategy từ tên
REPORT_REGISTRY = {
    'revenue': RevenueReport,
    'bestseller': BestSellerReport,
}


def get_report_strategy(report_type: str) -> ReportStrategy:
    """Factory function — DIP compliant."""
    cls = REPORT_REGISTRY.get(report_type, RevenueReport)
    return cls()
