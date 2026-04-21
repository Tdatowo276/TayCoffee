from models.db_client import execute_query, execute_insert_returning

CATEGORY_MAP = {
    'cà phê': 1,
    'trà': 2,
    'bánh ngọt': 3,
    'khác': 4,
}

def get_all_products():
    """SELECT tất cả sản phẩm đang hoạt động từ bảng Products"""
    sql = "SELECT * FROM Products WHERE isactive = True AND description NOT LIKE 'DELETED::%%' ORDER BY productid DESC"
    return execute_query(sql, fetch=True)

def update_product_stock(product_id, quantity):
    """Giảm tồn kho trực tiếp (dành cho hàng đóng gói)."""
    sql_check = "SELECT stockquantity FROM Products WHERE productid = %s"
    rows = execute_query(sql_check, [product_id], fetch=True)
    if not rows:
        return False

    current_stock = int(rows[0]['stockquantity'] or 0)
    if current_stock < quantity:
        return False

    new_stock = current_stock - quantity
    sql_update = "UPDATE Products SET stockquantity = %s WHERE productid = %s"
    return execute_query(sql_update, [new_stock, product_id])

def update_product_image_url(product_id, image_url):
    sql = "UPDATE Products SET imageurl = %s WHERE productid = %s"
    return execute_query(sql, [image_url, product_id])

def update_product_metadata(product_id, **kwargs):
    """Update product fields."""
    updates = {}
    if 'name' in kwargs: updates['productname'] = kwargs['name']
    if 'price' in kwargs: updates['price'] = float(kwargs['price'])
    if 'description' in kwargs: updates['description'] = kwargs['description']
    if 'image_url' in kwargs: updates['imageurl'] = kwargs['image_url']
    if 'is_active' in kwargs: updates['isactive'] = bool(kwargs['is_active'])
    
    if 'category_id' in kwargs:
        cat_id = kwargs['category_id']
        if isinstance(cat_id, str):
            cat_id = CATEGORY_MAP.get(cat_id.lower(), 4)
        updates['categoryid'] = int(cat_id)

    if not updates:
        return True

    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    sql = f"UPDATE Products SET {set_clause} WHERE productid = %s"
    params = list(updates.values()) + [product_id]
    return execute_query(sql, params)

def create_product(**kwargs):
    """Create a new product."""
    name = kwargs.get('name', 'New Coffee Item')
    price = float(kwargs.get('price', 0))
    desc = kwargs.get('description', '')
    img = kwargs.get('image_url') or kwargs.get('emoji', '☕')
    cat_id = kwargs.get('category_id', 1)
    if isinstance(cat_id, str):
        cat_id = CATEGORY_MAP.get(cat_id.lower(), 4)

    sql = """
        INSERT INTO Products (productname, price, description, imageurl, categoryid, isactive, stockquantity)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    params = (name, price, desc, img, int(cat_id), True, 100)
    return execute_insert_returning(sql, params)

def delete_product(product_id):
    """Soft delete."""
    sql = "UPDATE Products SET isactive = False, description = CONCAT('DELETED::', description) WHERE productid = %s"
    try:
        execute_query(sql, [product_id])
        return True, "Product hidden successfully"
    except Exception as e:
        return False, str(e)

