from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List
from models.db_client import execute_query, execute_insert_returning

TWOPLACES = Decimal('0.01')

def _quantize_money(value: Decimal) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

def get_all_tables():
    """Lấy danh sách bàn và trạng thái hiện tại."""
    sql = "SELECT * FROM Tables ORDER BY tablenumber"
    return execute_query(sql, fetch=True)

def get_inventory_status():
    """Lấy danh sách nguyên liệu và mức tồn kho."""
    sql = "SELECT * FROM Ingredients ORDER BY ingredientname"
    return execute_query(sql, fetch=True)

def deduct_ingredients(order_id: int):
    """Trừ nguyên liệu dựa trên công thức (Recipe) của các món trong đơn hàng."""
    try:
        # 1. Lấy chi tiết các món trong đơn hàng
        items = execute_query("SELECT productid, quantity FROM OrderDetails WHERE orderid = %s", [order_id], fetch=True)
        for item in items:
            product_id = item['productid']
            qty_sold = item['quantity']
            
            # 2. Lấy công thức cho món này
            recipe = execute_query("SELECT ingredientid, quantityneeded FROM Recipes WHERE productid = %s", [product_id], fetch=True)
            for r in recipe:
                ing_id = r['ingredientid']
                needed_per_unit = float(r['quantityneeded'])
                total_needed = needed_per_unit * qty_sold
                
                # 3. Cập nhật kho nguyên liệu
                execute_query(
                    "UPDATE Ingredients SET stockamount = stockamount - %s WHERE ingredientid = %s",
                    [total_needed, ing_id]
                )
        return True
    except Exception as e:
        print(f"Lỗi khi trừ nguyên liệu: {e}")
        return False

def get_all_orders(limit: int = 200):
    sql = """
        SELECT o.*, u.fullname as customer_name, t.tablenumber,
               (SELECT STRING_AGG(od2.quantity || 'x ' || p2.productname, ', ' ORDER BY od2.orderdetailid)
                FROM OrderDetails od2
                JOIN Products p2 ON od2.productid = p2.productid
                WHERE od2.orderid = o.orderid
               ) AS items_summary
        FROM Orders o
        LEFT JOIN Users u ON o.customerid = u.userid
        LEFT JOIN Tables t ON o.tableid = t.tableid
        ORDER BY o.orderdate DESC LIMIT %s
    """
    return execute_query(sql, [limit], fetch=True)

def update_order_status(order_id, status, employee_id=None):
    sql = "UPDATE Orders SET orderstatus = %s"
    params = [status]
    if employee_id:
        sql += ", employeeid = %s"
        params.append(employee_id)
    sql += " WHERE orderid = %s"
    params.append(order_id)
    return execute_query(sql, params)

def create_order(*, table_id=None, customer_id=None, employee_id=None, items: List[Dict], promotion_code=None, notes=None, payment_method='Cash'):
    # 1. Tính toán giá trị đơn hàng
    subtotal = Decimal('0.00')
    line_items = []
    
    for item in items:
        p_id = item['product_id']
        qty = item['quantity']
        product = execute_query("SELECT productname, price FROM Products WHERE productid = %s", [p_id], fetch=True)
        if not product: continue
        
        price = Decimal(str(product[0]['price']))
        subtotal += price * qty
        line_items.append({
            'product_id': p_id,
            'quantity': qty,
            'unit_price': price,
            'note': item.get('note', '')
        })

    # 2. Xử lý khuyến mãi (đơn giản hóa)
    discount = Decimal('0.00')
    promo_id = None
    if promotion_code:
        promo = execute_query("SELECT promotionid, discounttype, discountvalue FROM Promotions WHERE code = %s AND isactive = True", [promotion_code.upper()], fetch=True)
        if promo:
            promo_id = promo[0]['promotionid']
            val = Decimal(str(promo[0]['discountvalue']))
            if promo[0]['discounttype'] == 'percent':
                discount = subtotal * (val / 100)
            else:
                discount = val

    subtotal = _quantize_money(subtotal)
    discount = _quantize_money(discount)
    total = subtotal - discount
    if total < 0: total = Decimal('0.00')

    # 3. Tạo đơn hàng
    sql_order = """
        INSERT INTO Orders (customerid, tableid, employeeid, promotionid, subtotal, discount, orderstatus, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING orderid
    """
    order_data = execute_insert_returning(sql_order, (customer_id, table_id, employee_id, promo_id, float(subtotal), float(discount), 'pending', notes))
    if not order_data:
        return None
    order_id = order_data['orderid']

    # 4. Tạo chi tiết đơn hàng
    for li in line_items:
        execute_query(
            "INSERT INTO OrderDetails (orderid, productid, quantity, unitprice, ordernote) VALUES (%s, %s, %s, %s, %s)",
            (order_id, li['product_id'], li['quantity'], float(li['unit_price']), li['note'])
        )

    # 5. Khởi tạo thanh toán
    execute_query(
        "INSERT INTO Payments (orderid, amount, method, status) VALUES (%s, %s, %s, %s)",
        (order_id, float(_quantize_money(total)), payment_method, 'unpaid')
    )

    # 6. TỰ ĐỘNG TRỪ NGUYÊN LIỆU TRONG KHO
    deduct_ingredients(order_id)

    # 7. Cập nhật trạng thái bàn nếu có
    if table_id:
        execute_query("UPDATE Tables SET status = 'Occupied' WHERE tableid = %s", [table_id])

    return order_id
