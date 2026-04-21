from flask import Blueprint, render_template

cashier_bp = Blueprint('cashier', __name__)

@cashier_bp.route('/cashier/dashboard')
def cashier_dashboard():
    """Giao diện Thu ngân - quản lý đơn hàng và khách hàng."""
    return render_template('cashier/dashboard.html')
