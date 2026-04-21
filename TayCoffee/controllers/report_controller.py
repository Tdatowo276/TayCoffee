"""
Controller: ReportController — Implements IReportService (IBaoCao).
DIP: Nhận ReportStrategy qua constructor, KHÔNG dùng if-else.
"""
from datetime import date
from interfaces.business import IReportService
from interfaces.strategies import ReportStrategy, get_report_strategy


class ReportController(IReportService):
    """Controller tạo báo cáo — DIP compliant.
    Nhận strategy qua constructor, không tạo trực tiếp.
    """

    def __init__(self, strategy: ReportStrategy = None):
        """DIP: Nhận ReportStrategy qua constructor."""
        self._strategy = strategy

    def set_strategy(self, strategy: ReportStrategy):
        """Cho phép thay đổi strategy khi cần."""
        self._strategy = strategy

    def generate_report(self, from_date: date, to_date: date) -> dict:
        """taoBaoCao() — Tạo báo cáo theo strategy đã inject."""
        if not self._strategy:
            return {'ok': False, 'error': 'Chưa chọn loại báo cáo'}
        result = self._strategy.generate(from_date, to_date)
        return {'ok': True, 'report': result}

    def report_name(self) -> str:
        """tenBaoCao()"""
        if not self._strategy:
            return 'N/A'
        return self._strategy.report_name()

    @staticmethod
    def create_with_type(report_type: str) -> 'ReportController':
        """Factory: Tạo ReportController với strategy tương ứng.
        Sử dụng registry (không if-else).
        """
        strategy = get_report_strategy(report_type)
        return ReportController(strategy)
