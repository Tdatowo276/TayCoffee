"""
Controller: EmployeeController — Implements IEmployeeService (IQuanLyNhanVien).
"""
from interfaces.business import IEmployeeService
from entities.employee import Employee, Cashier, Manager
from models.db_client import execute_query, execute_insert_returning
from models.users import hash_password, get_user_by_email, get_user_by_id


ROLE_NAME_TO_ID = {'admin': 1, 'cashier': 2, 'staff': 3}
ROLE_ID_TO_NAME = {v: k for k, v in ROLE_NAME_TO_ID.items()}


class EmployeeController(IEmployeeService):
    """Controller quản lý nhân viên — CRUD operations."""

    def add_employee(self, employee_data: dict) -> dict:
        """themNV() — Thêm nhân viên."""
        full_name = employee_data.get('full_name', '').strip()
        email = employee_data.get('email', '').strip().lower()
        phone = employee_data.get('phone', '').strip() or None
        password = employee_data.get('password', '')
        role = employee_data.get('role', 'staff')

        if not full_name or not email or not password:
            return {'ok': False, 'error': 'Thiếu thông tin bắt buộc'}

        if get_user_by_email(email):
            return {'ok': False, 'error': 'Email đã tồn tại'}

        role_id = ROLE_NAME_TO_ID.get(role, 3)
        pw_hash = hash_password(password)

        sql = """INSERT INTO Users (fullname, email, phone, passwordhash, roleid)
                 VALUES (%s, %s, %s, %s, %s) RETURNING userid"""
        result = execute_insert_returning(sql, (full_name, email, phone, pw_hash, role_id))
        if not result:
            return {'ok': False, 'error': 'Không thể tạo nhân viên'}

        # Tạo Entity phù hợp dựa trên role (LSP)
        if role_id == 2:
            emp = Cashier(str(result['userid']), full_name, phone or '')
        elif role_id == 1:
            emp = Manager(str(result['userid']), full_name, phone or '')
        else:
            emp = Employee(str(result['userid']), full_name, 'Staff', phone or '')

        return {'ok': True, 'employee': emp.to_dict()}

    def update_employee(self, employee_data: dict) -> dict:
        """suaNV() — Cập nhật thông tin nhân viên."""
        user_id = employee_data.get('id')
        if not user_id:
            return {'ok': False, 'error': 'Thiếu ID nhân viên'}

        current = get_user_by_id(int(user_id))
        if not current:
            return {'ok': False, 'error': 'Nhân viên không tồn tại'}

        updates = {}
        if employee_data.get('full_name'):
            updates['fullname'] = employee_data['full_name'].strip()
        if 'phone' in employee_data:
            updates['phone'] = (employee_data['phone'] or '').strip() or None
        if employee_data.get('password'):
            updates['passwordhash'] = hash_password(employee_data['password'])
        if employee_data.get('role'):
            role_id = ROLE_NAME_TO_ID.get(employee_data['role'])
            if role_id:
                updates['roleid'] = role_id

        if not updates:
            return {'ok': False, 'error': 'Không có thông tin cập nhật'}

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        sql = f"UPDATE Users SET {set_clause} WHERE userid = %s"
        params = list(updates.values()) + [int(user_id)]
        execute_query(sql, params)

        return {'ok': True}

    def remove_employee(self, employee_id: str) -> dict:
        """xoaNV() — Vô hiệu hóa nhân viên (soft delete)."""
        user = get_user_by_id(int(employee_id))
        if not user:
            return {'ok': False, 'error': 'Nhân viên không tồn tại'}

        if int(user.get('roleid', 0)) == ROLE_NAME_TO_ID['admin']:
            return {'ok': False, 'error': 'Không thể xóa tài khoản Admin'}

        execute_query(
            "UPDATE Users SET isactive = False WHERE userid = %s",
            [int(employee_id)]
        )
        return {'ok': True, 'message': 'Đã vô hiệu hóa nhân viên'}
