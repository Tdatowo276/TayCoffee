"""
Controller: PaymentController — Implements IPaymentService (IThanhToan).
Luồng thanh toán theo Sequence Diagram 4.2.
DIP: Nhận PaymentMethod qua constructor (không if-else).
"""
from datetime import datetime
from interfaces.business import IPaymentService
from interfaces.strategies import PaymentMethod, get_payment_method
from entities.invoice import Invoice
from entities.order import Order
from models.db_client import execute_query


class PaymentController(IPaymentService):
    """Controller xử lý luồng thanh toán.
    
    Sequence Flow 4.2:
    1. PaymentForm -> PaymentController.get_order_info(order_id)
    2. PaymentController -> DonHang.get_details() + DonHang.calculate_total()
    3. User thanh toán: PaymentForm -> PaymentController.process_payment()
    4. PaymentController -> HoaDon.create() + HoaDon.calculate_final()
    5. PaymentController -> return result
    6. PaymentForm -> in hóa đơn
    """

    def __init__(self, payment_method: PaymentMethod = None):
        """DIP: Nhận PaymentMethod qua constructor."""
        self._payment_method = payment_method

    def get_order_info(self, order_id: str) -> dict:
        """Bước 1-2: Lấy thông tin đơn hàng."""
        order_row = execute_query(
            "SELECT * FROM Orders WHERE orderid = %s", [order_id], fetch=True
        )
        if not order_row:
            return {'ok': False, 'error': 'Đơn hàng không tồn tại'}

        order = Order.from_db_row(order_row[0])

        # Lấy chi tiết
        details = execute_query(
            """SELECT od.*, p.productname FROM OrderDetails od
               JOIN Products p ON od.productid = p.productid
               WHERE od.orderid = %s""",
            [order_id], fetch=True
        )

        return {
            'ok': True,
            'order': order.to_dict(),
            'details': details,
            'total': order.total
        }

    def process_payment(self, order_id: str, payment_method=None):
        """Bước 3-5: Xử lý thanh toán.
        DIP: payment_method nhận qua tham số hoặc constructor.
        """
        method = payment_method or self._payment_method
        if isinstance(method, str):
            method = get_payment_method(method)
        if method is None:
            method = get_payment_method('Cash')

        # Lấy thông tin đơn hàng
        order_row = execute_query(
            "SELECT * FROM Orders WHERE orderid = %s", [order_id], fetch=True
        )
        if not order_row:
            return {'ok': False, 'error': 'Đơn hàng không tồn tại'}

        total = float(order_row[0].get('subtotal', 0)) - float(order_row[0].get('discount', 0))

        # Bước 4: PaymentMethod xử lý thanh toán (đa hình, không if-else)
        paid_amount = method.pay(total)

        # Cập nhật trạng thái thanh toán
        execute_query(
            "UPDATE Payments SET status = 'paid', paidat = %s WHERE orderid = %s",
            [datetime.now(), order_id]
        )

        # Cập nhật trạng thái đơn hàng
        execute_query(
            "UPDATE Orders SET orderstatus = 'completed' WHERE orderid = %s",
            [order_id]
        )

        # Giải phóng bàn
        table_id = order_row[0].get('tableid')
        if table_id:
            execute_query(
                "UPDATE Tables SET status = 'Empty' WHERE tableid = %s",
                [table_id]
            )

        # Tạo hóa đơn
        invoice = Invoice(
            invoice_id=str(order_id),
            payment_date=datetime.now(),
            total=paid_amount,
            payment_method=method.method_name()
        )

        return {
            'ok': True,
            'invoice': invoice.to_dict(),
            'paid_amount': paid_amount,
            'method': method.method_name()
        }

    def apply_discount(self, order_id: str, promo_code: str):
        """Áp dụng mã giảm giá."""
        promo = execute_query(
            "SELECT promotionid, discounttype, discountvalue FROM Promotions WHERE code = %s AND isactive = True",
            [promo_code.upper()], fetch=True
        )
        if not promo:
            return {'ok': False, 'error': 'Mã khuyến mãi không hợp lệ'}

        order_row = execute_query(
            "SELECT subtotal FROM Orders WHERE orderid = %s", [order_id], fetch=True
        )
        if not order_row:
            return {'ok': False, 'error': 'Đơn hàng không tồn tại'}

        subtotal = float(order_row[0]['subtotal'])
        val = float(promo[0]['discountvalue'])
        discount = subtotal * (val / 100) if promo[0]['discounttype'] == 'percent' else val

        execute_query(
            "UPDATE Orders SET discount = %s, promotionid = %s WHERE orderid = %s",
            [discount, promo[0]['promotionid'], order_id]
        )

        return {'ok': True, 'discount': discount}

    def print_invoice(self, invoice_id: str) -> dict:
        """In hóa đơn."""
        payment = execute_query(
            "SELECT * FROM Payments WHERE orderid = %s", [invoice_id], fetch=True
        )
        if not payment:
            return {'ok': False, 'error': 'Hóa đơn không tồn tại'}

        invoice = Invoice.from_db_row(payment[0])
        return {'ok': True, 'invoice': invoice.to_dict()}
