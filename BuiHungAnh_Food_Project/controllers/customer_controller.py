from flask import Blueprint, current_app, jsonify, render_template, request
from models.db_client import execute_query
from models.products import get_all_products, update_product_image_url, update_product_metadata, create_product, delete_product
from models.orders import create_order, get_all_orders, update_order_status
from models.users import get_all_users, get_user_by_email, hash_password, insert_user, verify_password

customer_bp = Blueprint('customer', __name__)

def _resolve_role(role_id: int) -> str:
    if role_id == 1: return 'admin'
    if role_id == 2: return 'cashier'
    return 'staff'

def _serialize_auth_user(user: dict) -> dict:
    role_id = int(user.get('roleid') or 3)
    return {
        "id": user.get('userid'),
        "name": user.get('fullname'),
        "email": user.get('email'),
        "phone": user.get('phone'),
        "role": _resolve_role(role_id),
        "role_id": role_id,
    }

@customer_bp.route('/')
@customer_bp.route('/index.html')
def homepage_file():
    return render_template('index.html')

@customer_bp.route('/api/health', methods=['GET'])
def api_health():
    """Health check for Postgres."""
    try:
        ping = execute_query("SELECT 1", fetch=True)
        return jsonify({"ok": True, "database": "postgresql", "status": "connected" if ping else "error"}), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

@customer_bp.route('/api/users', methods=['GET'])
def api_users():
    limit = request.args.get('limit', default=20, type=int)
    data = get_all_users(limit)
    return jsonify({"count": len(data), "items": data}), 200

@customer_bp.route('/api/products', methods=['GET'])
def api_products():
    limit = request.args.get('limit', default=20, type=int)
    data = get_all_products()[:limit]
    return jsonify({"count": len(data), "items": data}), 200

@customer_bp.route('/api/orders', methods=['GET'])
def api_orders():
    limit = request.args.get('limit', default=20, type=int)
    data = get_all_orders(limit)
    return jsonify({"count": len(data), "items": data}), 200

@customer_bp.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    password = (payload.get('password') or '').strip()
    
    print(f"DEBUG: Login attempt for email: '{email}'")
    user = get_user_by_email(email)
    
    if not user:
        print(f"DEBUG: User '{email}' not found in database.")
        return jsonify({"ok": False, "error": "Tài khoản không tồn tại"}), 401
    
    match = verify_password(password, user.get('passwordhash'))
    if not match:
        print(f"DEBUG: Password mismatch for user '{email}'.")
        print(f"DEBUG: Input: {password} -> Hash: {hash_password(password)}")
        print(f"DEBUG: Stored: {user.get('passwordhash')}")
        return jsonify({"ok": False, "error": "Mật khẩu không chính xác"}), 401
    
    print(f"DEBUG: Login successful for user '{email}'")
    return jsonify({"ok": True, "user": _serialize_auth_user(user)}), 200

@customer_bp.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    payload = request.get_json(silent=True) or {}
    full_name = payload.get('full_name', '').strip()
    email = payload.get('email', '').strip().lower()
    password = payload.get('password', '')
    
    if get_user_by_email(email):
        return jsonify({"ok": False, "error": "Email already exists"}), 409
        
    new_id = insert_user(full_name, email, hash_password(password), role_id=3)
    return jsonify({"ok": True, "user_id": new_id}), 201
