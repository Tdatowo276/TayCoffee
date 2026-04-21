"""
Controller: OrderController — Implements IOrderService (IGoiMon).
Luồng gọi món theo Sequence Diagram 4.1.
DIP: Nhận dependency qua constructor, KHÔNG khởi tạo trực tiếp.
"""
from interfaces.business import IOrderService
from entities.order import Order, OrderDetail
from entities.table import Table
from entities.product import Product
from models.db_client import execute_query, execute_insert_returning
from models.orders import deduct_ingredients
from decimal import Decimal, ROUND_HALF_UP


class OrderController(IOrderService):
    """Controller xử lý luồng gọi món.
    
    Sequence Flow 4.1:
    1. OrderForm -> OrderController.create_order(table_id)
    2. OrderController -> Table.get_info(table_id)
    3. User thêm món: OrderForm -> OrderController.add_item(...)
    4. OrderController -> Product.get_info(product_id)
    5. OrderController -> Order.add_product(...)
    6. User xác nhận: OrderForm -> OrderController.confirm_order()
    7. OrderController -> Order.save() + Table.update_status('Occupied')
    8. OrderController -> return success
    """

    def __init__(self):
        self._current_order = None
        self._current_table = None

    def create_order(self, table_id: str):
        """Bước 1-2: Tạo đơn hàng mới cho bàn."""
        # Bước 2: Kiểm tra bàn
        table_row = execute_query(
            "SELECT * FROM Tables WHERE tableid = %s", [table_id], fetch=True
        )
        if not table_row:
            return {'ok': False, 'error': 'Bàn không tồn tại'}

        self._current_table = Table.from_db_row(table_row[0])
        self._current_order = Order(order_id='new', status='pending')

        return {'ok': True, 'table': self._current_table.to_dict()}

    def add_item(self, order_id: str, product_id: str,
                 quantity: int, note: str = ''):
        """Bước 3-5: Thêm món vào đơn hàng."""
        # Bước 4: Lấy thông tin sản phẩm
        product_row = execute_query(
            "SELECT * FROM Products WHERE productid = %s AND isactive = True",
            [product_id], fetch=True
        )
        if not product_row:
            return {'ok': False, 'error': 'Sản phẩm không tồn tại'}

        product = Product.from_db_row(product_row[0])

        # Bước 5: Thêm vào đơn hàng
        if self._current_order:
            self._current_order.add_product(
                product.product_id, quantity, product.price, note
            )

        return {'ok': True, 'product': product.to_dict(), 'quantity': quantity}

    def remove_item(self, order_id: str, product_id: str):
        """Xóa món khỏi đơn hàng."""
        if self._current_order:
            self._current_order.remove_product(product_id)
        return {'ok': True}

    def confirm_order(self, *, table_id=None, customer_id=None,
                      employee_id=None, items: list, promotion_code=None,
                      notes=None, payment_method='Cash'):
        """Bước 6-8: Xác nhận và lưu đơn hàng."""
        # Tính toán giá trị
        subtotal = Decimal('0.00')
        line_items = []

        for item in items:
            p_id = item['product_id']
            qty = item['quantity']
            product = execute_query(
                "SELECT productname, price FROM Products WHERE productid = %s",
                [p_id], fetch=True
            )
            if not product:
                continue

            price = Decimal(str(product[0]['price']))
            subtotal += price * qty
            line_items.append({
                'product_id': p_id,
                'quantity': qty,
                'unit_price': price,
                'note': item.get('note', '')
            })

        # Xử lý khuyến mãi
        discount = Decimal('0.00')
        promo_id = None
        if promotion_code:
            promo = execute_query(
                "SELECT promotionid, discounttype, discountvalue FROM Promotions WHERE code = %s AND isactive = True",
                [promotion_code.upper()], fetch=True
            )
            if promo:
                promo_id = promo[0]['promotionid']
                val = Decimal(str(promo[0]['discountvalue']))
                if promo[0]['discounttype'] == 'percent':
                    discount = subtotal * (val / 100)
                else:
                    discount = val

        subtotal = subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discount = discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total = subtotal - discount
        if total < 0:
            total = Decimal('0.00')

        # Bước 7: Lưu đơn hàng
        sql_order = """
            INSERT INTO Orders (customerid, tableid, employeeid, promotionid, subtotal, discount, orderstatus, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING orderid
        """
        order_data = execute_insert_returning(sql_order, (
            customer_id, table_id, employee_id, promo_id,
            float(subtotal), float(discount), 'pending', notes
        ))
        if not order_data:
            return None
        order_id = order_data['orderid']

        # Lưu chi tiết
        for li in line_items:
            execute_query(
                "INSERT INTO OrderDetails (orderid, productid, quantity, unitprice, ordernote) VALUES (%s, %s, %s, %s, %s)",
                (order_id, li['product_id'], li['quantity'], float(li['unit_price']), li['note'])
            )

        # Khởi tạo thanh toán
        execute_query(
            "INSERT INTO Payments (orderid, amount, method, status) VALUES (%s, %s, %s, %s)",
            (order_id, float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), payment_method, 'unpaid')
        )

        # Trừ nguyên liệu tự động
        deduct_ingredients(order_id)

        # Bước 7: Cập nhật trạng thái bàn
        if table_id:
            execute_query(
                "UPDATE Tables SET status = 'Occupied' WHERE tableid = %s", [table_id]
            )

        return order_id
