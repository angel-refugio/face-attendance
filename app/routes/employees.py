import os
import shutil
import logging
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required
from app.extensions import db
from app.models.employee import Employee
from app.services.face_service import entrenar_modelo

logger = logging.getLogger(__name__)

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("/")
@login_required
def list_employees():
    employees = Employee.query.order_by(Employee.name).all()
    return render_template("employees.html", employees=employees)


@employees_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_employee():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        position = request.form.get("position", "").strip()
        email = request.form.get("email", "").strip()
        work_days_list = request.form.getlist("work_days")
        work_start_time = request.form.get("work_start_time", "09:00")

        if not name:
            flash("El nombre es obligatorio", "error")
            return redirect(url_for("employees.add_employee"))

        if Employee.query.filter_by(name=name).first():
            flash(f"Ya existe un empleado con el nombre '{name}'", "error")
            return redirect(url_for("employees.add_employee"))

        work_days = ",".join(work_days_list) if work_days_list else "1,2,3,4,5"

        employee = Employee(
            name=name,
            department=department or None,
            position=position or None,
            email=email or None,
            work_days=work_days,
            work_start_time=work_start_time,
        )
        db.session.add(employee)
        db.session.commit()

        flash(f"Empleado '{name}' agregado correctamente", "success")
        return redirect(url_for("employees.list_employees"))

    return render_template("employee_form.html", employee=None)


@employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)

    if request.method == "POST":
        employee.name = request.form.get("name", "").strip()
        employee.department = request.form.get("department", "").strip() or None
        employee.position = request.form.get("position", "").strip() or None
        employee.email = request.form.get("email", "").strip() or None
        
        work_days_list = request.form.getlist("work_days")
        employee.work_days = ",".join(work_days_list) if work_days_list else "1,2,3,4,5"
        employee.work_start_time = request.form.get("work_start_time", "09:00")

        db.session.commit()
        flash(f"Empleado '{employee.name}' actualizado", "success")
        return redirect(url_for("employees.list_employees"))

    return render_template("employee_form.html", employee=employee)


@employees_bp.route("/<int:employee_id>/delete", methods=["POST"])
@login_required
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    name = employee.name

    faces_dir = current_app.config["FACES_DIR"]
    face_folder = os.path.join(faces_dir, name)
    if os.path.exists(face_folder):
        shutil.rmtree(face_folder)
        logger.info(f"Carpeta de rostros eliminada: {face_folder}")

    db.session.delete(employee)
    db.session.commit()

    flash(f"Empleado '{name}' eliminado", "success")
    return redirect(url_for("employees.list_employees"))


@employees_bp.route("/<int:employee_id>/toggle-status", methods=["POST"])
@login_required
def toggle_status(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    employee.status = "inactive" if employee.status == "active" else "active"
    db.session.commit()

    status_text = "desactivado" if employee.status == "inactive" else "activado"
    flash(f"Empleado '{employee.name}' {status_text}", "success")
    return redirect(url_for("employees.list_employees"))


@employees_bp.route("/retrain", methods=["POST"])
@login_required
def retrain_model():
    success = entrenar_modelo()
    if success:
        flash("Modelo reentrenado correctamente", "success")
    else:
        flash("Error al reentrenar el modelo", "error")
    return redirect(url_for("employees.list_employees"))
