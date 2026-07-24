import logging
from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db
from app.models.employee import Employee
from app.models.attendance import AttendanceRecord

logger = logging.getLogger(__name__)


def check_in_employee(employee_name, confidence_score):
    employee = Employee.query.filter_by(name=employee_name, status="active").first()
    if not employee:
        logger.warning(f"Empleado no encontrado: {employee_name}")
        return None, "Empleado no encontrado"

    if not employee.should_work_today():
        logger.info(f"Empleado {employee_name} no trabaja hoy")
        return None, "No es día laboral para este empleado"

    duplicate_window = current_app.config.get("DUPLICATE_WINDOW_MINUTES", 5)
    cutoff = datetime.now() - timedelta(minutes=duplicate_window)

    recent = (
        AttendanceRecord.query.filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.check_in_time >= cutoff,
        )
        .order_by(AttendanceRecord.check_in_time.desc())
        .first()
    )

    if recent:
        logger.info(f"Check-in duplicado ignorado para {employee_name}")
        return recent, "Ya registrado recientemente"

    now = datetime.now()
    
    try:
        work_time_parts = employee.work_start_time.split(":")
        work_hour = int(work_time_parts[0])
        work_minute = int(work_time_parts[1]) if len(work_time_parts) > 1 else 0
    except (ValueError, IndexError, AttributeError):
        work_hour = 9
        work_minute = 0
        logger.warning(f"Formato de hora invalido para {employee_name}: {employee.work_start_time}")

    work_start = now.replace(hour=work_hour, minute=work_minute, second=0, microsecond=0)

    if now > work_start:
        status = "late"
    else:
        status = "on_time"

    record = AttendanceRecord(
        employee_id=employee.id,
        check_in_time=now,
        confidence_score=confidence_score,
        status=status,
    )
    db.session.add(record)
    db.session.commit()

    logger.info(
        f"Check-in registrado: {employee_name} a las {now.strftime('%H:%M:%S')} ({status})"
    )
    return record, "Check-in exitoso"


def get_today_attendance():
    today = datetime.now().date()
    records = (
        AttendanceRecord.query.filter(
            db.func.date(AttendanceRecord.check_in_time) == today
        )
        .order_by(AttendanceRecord.check_in_time.desc())
        .all()
    )
    return records


def get_attendance_by_date_range(start_date, end_date):
    records = (
        AttendanceRecord.query.filter(
            AttendanceRecord.check_in_time >= start_date,
            AttendanceRecord.check_in_time <= end_date,
        )
        .order_by(AttendanceRecord.check_in_time.desc())
        .all()
    )
    return records


def get_attendance_stats():
    today = datetime.now().date()
    today_records = (
        AttendanceRecord.query.filter(
            db.func.date(AttendanceRecord.check_in_time) == today
        )
        .all()
    )

    total_today = len(today_records)
    on_time = sum(1 for r in today_records if r.status == "on_time")
    late = sum(1 for r in today_records if r.status == "late")

    total_employees = Employee.query.filter_by(status="active").count()

    return {
        "total_today": total_today,
        "on_time": on_time,
        "late": late,
        "total_employees": total_employees,
        "attendance_rate": round((total_today / total_employees * 100), 1)
        if total_employees > 0
        else 0,
    }
