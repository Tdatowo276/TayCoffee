"""
Controller: InventoryController — Implements IInventoryService (IQuanLyKho).
"""
from interfaces.business import IInventoryService
from entities.ingredient import Ingredient
from entities.import_receipt import ImportReceipt
from models.db_client import execute_query


class InventoryController(IInventoryService):
    """Controller quản lý kho nguyên liệu."""

    def import_stock(self, receipt: ImportReceipt) -> bool:
        """nhapKho() — Nhập kho từ phiếu nhập."""
        for item in receipt.items:
            execute_query(
                "UPDATE Ingredients SET stockamount = stockamount + %s WHERE ingredientid = %s",
                [item.quantity, item.ingredient_id]
            )
        return True

    def check_inventory(self) -> list:
        """kiemTraTonKho() — Liệt kê tình trạng kho."""
        rows = execute_query(
            "SELECT * FROM Ingredients ORDER BY ingredientname", fetch=True
        )
        return [Ingredient.from_db_row(r).to_dict() for r in rows]

    def get_low_stock_alerts(self) -> list:
        """canhBao() — Danh sách NL sắp hết."""
        rows = execute_query(
            "SELECT * FROM Ingredients WHERE stockamount < minstockthreshold ORDER BY stockamount",
            fetch=True
        )
        return [Ingredient.from_db_row(r).to_dict() for r in rows]
