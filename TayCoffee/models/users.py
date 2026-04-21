import hashlib
from typing import Any, Optional
from models.db_client import execute_query, execute_insert_returning

ROLE_NAME_TO_ID = {
    'admin': 1,
    'cashier': 2,
    'staff': 3,
}

def _normalize_role_id(role: Any = None) -> Optional[int]:
    """Convert role input (int/str) to RoleID or None."""
    if role is None:
        return None
    if isinstance(role, (int, float)):
        role_int = int(role)
        return role_int if role_int in ROLE_NAME_TO_ID.values() else None
    role_name = str(role).strip().lower()
    return ROLE_NAME_TO_ID.get(role_name)

def hash_password(plain_password):
    """Hash mật khẩu bằng SHA-256 để lưu DB."""
    return hashlib.sha256(plain_password.encode('utf-8')).hexdigest()

def verify_password(input_password, stored_hash):
    """Kiểm tra mật khẩu nhập vào với dữ liệu đang có trong DB."""
    if not stored_hash:
        return False
    input_sha = hash_password(input_password)
    return stored_hash == input_sha

def get_all_users(limit: int = 500):
    return get_users(limit=limit)

def get_users(limit: int = 500, role: Any = None):
    """Flexible SELECT theo role / limit từ bảng Users."""
    sql = "SELECT userid, fullname, email, phone, roleid, isactive, createdat FROM Users"
    params = []
    
    role_id = _normalize_role_id(role)
    if role_id is not None:
        sql += " WHERE roleid = %s"
        params.append(role_id)
        sql += " AND email NOT LIKE 'del_%%'"
    else:
        sql += " WHERE email NOT LIKE 'del_%%'"
        
    sql += " ORDER BY userid DESC LIMIT %s"
    params.append(limit)
    
    return execute_query(sql, params, fetch=True)

def insert_user(full_name, email, password_hash, role_id=3, phone=None):
    """INSERT người dùng mới vào bảng Users"""
    sql = """
        INSERT INTO Users (fullname, email, phone, passwordhash, roleid)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING userid
    """
    params = (full_name, email, phone, password_hash, role_id)
    result = execute_insert_returning(sql, params)
    return result['userid'] if result else None

def get_user_by_email(email):
    """SELECT 1 người dùng theo email"""
    sql = "SELECT userid, fullname, email, phone, passwordhash, roleid, isactive FROM Users WHERE email = %s LIMIT 1"
    rows = execute_query(sql, [email], fetch=True)
    return rows[0] if rows else None

def get_user_by_id(user_id: int):
    sql = "SELECT userid, fullname, email, phone, roleid, isactive, createdat FROM Users WHERE userid = %s LIMIT 1"
    rows = execute_query(sql, [user_id], fetch=True)
    return rows[0] if rows else None

def update_user(user_id: int, **fields):
    """Update user fields."""
    allowed = {'fullname', 'phone', 'roleid', 'isactive', 'passwordhash', 'email'}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return False
    
    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    sql = f"UPDATE Users SET {set_clause} WHERE userid = %s"
    params = list(updates.values()) + [user_id]
    
    return execute_query(sql, params)

def delete_user(user_id: int):
    """Soft delete a user."""
    # First, get current email
    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"
    
    new_email = f"del_{user_id}_{user['email']}"
    sql = "UPDATE Users SET isactive = False, email = %s WHERE userid = %s"
    try:
        execute_query(sql, [new_email, user_id])
        return True, "User deleted (soft delete)"
    except Exception as e:
        return False, str(e)

def set_user_active(user_id: int, active: bool):
    """Enable or disable a user account."""
    sql = "UPDATE Users SET isactive = %s WHERE userid = %s"
    return execute_query(sql, [active, user_id])
