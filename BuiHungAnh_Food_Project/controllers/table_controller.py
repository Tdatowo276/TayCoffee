"""
Controller: TableController — Quản lý bàn.
Luồng theo Sequence Diagram 4.3.
"""
from entities.table import Table
from models.db_client import execute_query


class TableController:
    """Controller xử lý luồng quản lý bàn.
    
    Sequence Flow 4.3:
    1. TableUI -> TableController.get_all_tables()
    2. TableController -> Ban.get_data(). Trả về UI.
    3. User cập nhật: TableUI -> TableController.update_status(table_id, status)
    4. TableController -> Ban.update_status()
    5. Trả về success cho TableUI.
    """

    def get_all_tables(self) -> list:
        """Bước 1-2: Lấy danh sách tất cả các bàn."""
        rows = execute_query("SELECT * FROM Tables ORDER BY tablenumber", fetch=True)
        tables = [Table.from_db_row(r) for r in rows]
        return [t.to_dict() for t in tables if t]

    def get_table_info(self, table_id: str) -> dict:
        """Lấy thông tin chi tiết 1 bàn."""
        rows = execute_query(
            "SELECT * FROM Tables WHERE tableid = %s", [table_id], fetch=True
        )
        if not rows:
            return {'ok': False, 'error': 'Bàn không tồn tại'}

        table = Table.from_db_row(rows[0])
        return {'ok': True, 'table': table.to_dict()}

    def update_status(self, table_id: str, new_status: str) -> dict:
        """Bước 3-5: Cập nhật trạng thái bàn."""
        rows = execute_query(
            "SELECT * FROM Tables WHERE tableid = %s", [table_id], fetch=True
        )
        if not rows:
            return {'ok': False, 'error': 'Bàn không tồn tại'}

        table = Table.from_db_row(rows[0])
        if not table.update_status(new_status):
            return {'ok': False, 'error': f'Trạng thái "{new_status}" không hợp lệ'}

        # Lưu vào DB
        execute_query(
            "UPDATE Tables SET status = %s WHERE tableid = %s",
            [new_status, table_id]
        )

        return {'ok': True, 'table': table.to_dict()}
