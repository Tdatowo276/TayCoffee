"""
Boundaries Layer: Flask Blueprints & API Routes.
Bridge HTTP requests to Controllers.
"""
from flask import Blueprint, jsonify, request, session
from datetime import date

# Import Controllers
from controllers.order_controller import OrderController
from controllers.payment_controller import PaymentController
from controllers.table_controller import TableController
from controllers.inventory_controller import InventoryController
from controllers.employee_controller import EmployeeController
from controllers.report_controller import ReportController

# Initialize Blueprints
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Instantiate Controllers (Simple DI for now, could be improved with a container)
order_ctrl = OrderController()
payment_ctrl = PaymentController()
table_ctrl = TableController()
inventory_ctrl = InventoryController()
employee_ctrl = EmployeeController()

# ============================================================
# 1. AUTHENTICATION & USERS (Customer & Shared)
# ============================================================

@api_bp.route('/auth/login', methods=['POST'])
def login():
    from controllers.customer_controller import api_auth_login
    return api_auth_login() # Using legacy for now or refactor to use EmployeeController/Account

@api_bp.route('/auth/register', methods=['POST'])
def register():
    payload = request.get_json(silent=True) or {}
    return jsonify(employee_ctrl.add_employee(payload))

# ============================================================
# 2. PRODUCTS & INVENTORY
# ============================================================

@api_bp.route('/products', methods=['GET'])
def list_products():
    from models.products import get_all_products
    return jsonify({"ok": True, "items": get_all_products()})

@api_bp.route('/admin/inventory', methods=['GET'])
def get_inventory():
    return jsonify({"ok": True, "items": inventory_ctrl.check_inventory()})

@api_bp.route('/admin/inventory/alerts', methods=['GET'])
def get_inventory_alerts():
    return jsonify({"ok": True, "items": inventory_ctrl.get_low_stock_alerts()})

@api_bp.route('/admin/products', methods=['POST'])
def create_product():
    from models.products import create_product
    payload = request.get_json(silent=True) or {}
    return jsonify({"ok": True, "product": create_product(**payload)})

@api_bp.route('/admin/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    from models.products import update_product_metadata
    payload = request.get_json(silent=True) or {}
    success = update_product_metadata(product_id, **payload)
    if success:
        return jsonify({"ok": True, "message": "Product updated"})
    return jsonify({"ok": False, "error": "Failed to update product"}), 400

@api_bp.route('/admin/products/<product_id>', methods=['DELETE'])
def delete_product_route(product_id):
    from models.products import delete_product
    success, msg = delete_product(product_id)
    if success:
        return jsonify({"ok": True, "message": msg})
    return jsonify({"ok": False, "error": msg}), 400

# ============================================================
# 3. ORDERS & TABLES
# ============================================================

@api_bp.route('/orders', methods=['POST'])
def create_order():
    payload = request.get_json(silent=True) or {}
    order_id = order_ctrl.confirm_order(**payload)
    if order_id:
        return jsonify({"ok": True, "order_id": order_id}), 201
    return jsonify({"ok": False, "error": "Could not create order"}), 400

@api_bp.route('/orders', methods=['GET'])
def list_orders():
    from models.orders import get_all_orders
    limit = request.args.get('limit', default=100, type=int)
    return jsonify({"ok": True, "items": get_all_orders(limit)})

@api_bp.route('/admin/tables', methods=['GET'])
def list_tables():
    return jsonify({"ok": True, "items": table_ctrl.get_all_tables()})

@api_bp.route('/admin/tables/<table_id>', methods=['PUT'])
def update_table(table_id):
    payload = request.get_json(silent=True) or {}
    return jsonify(table_ctrl.update_status(table_id, payload.get('status')))

# ============================================================
# 4. PAYMENTS
# ============================================================

@api_bp.route('/payments/<order_id>', methods=['POST'])
def process_payment(order_id):
    payload = request.get_json(silent=True) or {}
    method = payload.get('method', 'Cash')
    return jsonify(payment_ctrl.process_payment(order_id, method))

# ============================================================
# 5. REPORTS
# ============================================================

@api_bp.route('/admin/reports/<report_type>', methods=['GET'])
def get_report(report_type):
    from_str = request.args.get('from', default=date.today().isoformat())
    to_str = request.args.get('to', default=date.today().isoformat())
    
    try:
        from_date = date.fromisoformat(from_str)
        to_date = date.fromisoformat(to_str)
        
        report_ctrl = ReportController.create_with_type(report_type)
        return jsonify(report_ctrl.generate_report(from_date, to_date))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

# ============================================================
# 6. ADMIN USER MANAGEMENT
# ============================================================

@api_bp.route('/admin/users', methods=['GET'])
def list_users():
    from models.users import get_users
    role = request.args.get('role')
    return jsonify({"ok": True, "items": get_users(role=role)})

@api_bp.route('/admin/users', methods=['POST'])
def admin_create_user():
    payload = request.get_json(silent=True) or {}
    return jsonify(employee_ctrl.add_employee(payload))

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "Tay Coffee BCE"}), 200
