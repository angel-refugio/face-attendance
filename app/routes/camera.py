import base64
import logging
import os
import numpy as np
import cv2
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from app.extensions import db
from app.models.employee import Employee
from app.services.face_service import (
    cargar_modelo,
    reconocer_rostro,
    guardar_rostro,
    entrenar_modelo,
)
from app.services.attendance_service import check_in_employee

logger = logging.getLogger(__name__)

camera_bp = Blueprint("camera", __name__)


@camera_bp.route("/")
@login_required
def camera_view():
    employees = Employee.query.filter_by(status="active").order_by(Employee.name).all()
    return render_template("camera.html", employees=employees)


@camera_bp.route("/register/<int:employee_id>")
@login_required
def register_face(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    return render_template("register_face.html", employee=employee)


@camera_bp.route("/api/recognize", methods=["POST"])
@login_required
def api_recognize():
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    try:
        image_data = data["image"].split(",")[1] if "," in data["image"] else data["image"]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Invalid image"}), 400

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        recognizer, label_map = cargar_modelo()
        if recognizer is None:
            return jsonify({"error": "Modelo no entrenado"}), 500

        results = reconocer_rostro(gray, recognizer, label_map)

        for result in results:
            if result["status"] == "recognized" and result["employee_name"]:
                record, message = check_in_employee(
                    result["employee_name"], result["confidence"]
                )
                result["check_in"] = {
                    "success": record is not None and message == "Check-in exitoso",
                    "message": message,
                    "time": record.check_in_time.strftime("%H:%M:%S") if record else None,
                    "status": record.status if record else None,
                }

        return jsonify({"results": results})

    except Exception as e:
        logger.error(f"Error en reconocimiento: {e}")
        return jsonify({"error": str(e)}), 500


@camera_bp.route("/api/capture/<int:employee_id>", methods=["POST"])
@login_required
def api_capture(employee_id):
    employee = Employee.query.get_or_404(employee_id)

    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    try:
        image_data = data["image"].split(",")[1] if "," in data["image"] else data["image"]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            logger.error("No se pudo decodificar la imagen")
            return jsonify({"error": "Invalid image"}), 400

        logger.info(f"Imagen recibida: {frame.shape}")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces_dir = current_app.config["FACES_DIR"]
        persona_dir = os.path.join(faces_dir, employee.name)
        existing = [f for f in os.listdir(persona_dir) if f.endswith(".jpg")] if os.path.exists(persona_dir) else []
        count = len(existing) + 1

        filepath = guardar_rostro(gray, employee.name, count)

        if filepath:
            employee.face_registered = True
            db.session.commit()
            return jsonify(
                {
                    "success": True,
                    "count": count,
                    "message": f"Foto {count} capturada",
                }
            )
        else:
            return jsonify({"success": False, "message": "No se detectó rostro. Asegúrate de tener buena iluminación y mirar de frente a la cámara."}), 400

    except Exception as e:
        logger.error(f"Error capturando rostro: {e}")
        return jsonify({"error": str(e)}), 500


@camera_bp.route("/api/train", methods=["POST"])
@login_required
def api_train():
    try:
        success = entrenar_modelo()
        if success:
            return jsonify({"success": True, "message": "Modelo entrenado correctamente"})
        else:
            return jsonify({"success": False, "message": "Error al entrenar"}), 500
    except Exception as e:
        logger.error(f"Error entrenando modelo: {e}")
        return jsonify({"error": str(e)}), 500


@camera_bp.route("/api/employee/<int:employee_id>/photos")
@login_required
def api_employee_photos(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    faces_dir = current_app.config["FACES_DIR"]
    persona_dir = os.path.join(faces_dir, employee.name)

    photos = []
    if os.path.exists(persona_dir):
        photos = sorted(
            [f for f in os.listdir(persona_dir) if f.endswith(".jpg")]
        )

    return jsonify({"count": len(photos), "photos": photos})
