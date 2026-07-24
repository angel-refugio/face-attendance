from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.models.employee import Employee
from app.services.attendance_service import get_today_attendance, get_attendance_stats

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    stats = get_attendance_stats()
    today_records = get_today_attendance()
    employees = Employee.query.filter_by(status="active").all()
    return render_template(
        "dashboard.html",
        stats=stats,
        today_records=today_records,
        employees=employees,
    )


@main_bp.route("/api/stats")
@login_required
def api_stats():
    stats = get_attendance_stats()
    return jsonify(stats)
