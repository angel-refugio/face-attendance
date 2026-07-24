import logging
from datetime import datetime, timedelta
from flask import (
    Blueprint,
    render_template,
    request,
    Response,
    current_app,
)
from flask_login import login_required
from app.models.employee import Employee
from app.models.attendance import AttendanceRecord
from app.extensions import db
from app.services.attendance_service import get_attendance_by_date_range
from app.services.report_service import export_attendance_csv, export_attendance_excel

logger = logging.getLogger(__name__)

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/")
@login_required
def history():
    page = request.args.get("page", 1, type=int)
    per_page = 20

    employee_id = request.args.get("employee_id", type=int)
    status = request.args.get("status")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    query = AttendanceRecord.query

    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if status:
        query = query.filter_by(status=status)
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(AttendanceRecord.check_in_time >= from_date)
        except ValueError:
            pass
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(AttendanceRecord.check_in_time < to_date)
        except ValueError:
            pass

    pagination = (
        query.order_by(AttendanceRecord.check_in_time.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    employees = Employee.query.filter_by(status="active").order_by(Employee.name).all()

    return render_template(
        "attendance.html",
        records=pagination.items,
        pagination=pagination,
        employees=employees,
        filters={
            "employee_id": employee_id,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
        },
    )


@attendance_bp.route("/export/csv")
@login_required
def export_csv():
    employee_id = request.args.get("employee_id", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    start_date = (
        datetime.strptime(date_from, "%Y-%m-%d")
        if date_from
        else datetime.now() - timedelta(days=30)
    )
    end_date = (
        datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        if date_to
        else datetime.now() + timedelta(days=1)
    )

    records = get_attendance_by_date_range(start_date, end_date)
    if employee_id:
        records = [r for r in records if r.employee_id == employee_id]

    csv_data = export_attendance_csv(records)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=asistencia.csv"},
    )


@attendance_bp.route("/export/excel")
@login_required
def export_excel():
    employee_id = request.args.get("employee_id", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    start_date = (
        datetime.strptime(date_from, "%Y-%m-%d")
        if date_from
        else datetime.now() - timedelta(days=30)
    )
    end_date = (
        datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        if date_to
        else datetime.now() + timedelta(days=1)
    )

    records = get_attendance_by_date_range(start_date, end_date)
    if employee_id:
        records = [r for r in records if r.employee_id == employee_id]

    excel_data = export_attendance_excel(records)
    if excel_data is None:
        return "openpyxl no instalado", 500

    return Response(
        excel_data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=asistencia.xlsx"},
    )


@attendance_bp.route("/stats")
@login_required
def stats():
    employees = Employee.query.filter_by(status="active").all()

    last_30_days = datetime.now() - timedelta(days=30)
    records = AttendanceRecord.query.filter(
        AttendanceRecord.check_in_time >= last_30_days
    ).all()

    daily_data = {}
    for record in records:
        date_str = record.check_in_time.strftime("%Y-%m-%d")
        if date_str not in daily_data:
            daily_data[date_str] = {"on_time": 0, "late": 0}
        if record.status == "on_time":
            daily_data[date_str]["on_time"] += 1
        else:
            daily_data[date_str]["late"] += 1

    sorted_dates = sorted(daily_data.keys())
    chart_labels = sorted_dates[-14:]
    chart_on_time = [daily_data[d]["on_time"] for d in chart_labels]
    chart_late = [daily_data[d]["late"] for d in chart_labels]

    employee_stats = []
    for emp in employees:
        emp_records = [r for r in records if r.employee_id == emp.id]
        total = len(emp_records)
        on_time = sum(1 for r in emp_records if r.status == "on_time")
        punctuality = round((on_time / total * 100), 1) if total > 0 else 0
        employee_stats.append(
            {
                "employee": emp,
                "total": total,
                "on_time": on_time,
                "late": total - on_time,
                "punctuality": punctuality,
            }
        )

    employee_stats.sort(key=lambda x: x["punctuality"], reverse=True)

    return render_template(
        "stats.html",
        chart_labels=chart_labels,
        chart_on_time=chart_on_time,
        chart_late=chart_late,
        employee_stats=employee_stats,
    )
