import os
import logging
import numpy as np
import cv2
from flask import current_app

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
FACE_CASCADE_PATH = os.path.join(DATA_DIR, "haarcascade_frontalface_default.xml")
EYE_CASCADE_PATH = os.path.join(DATA_DIR, "haarcascade_eye.xml")

face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)

if face_cascade.empty():
    logger.error(f"ERROR: No se pudo cargar el clasificador de rostros desde {FACE_CASCADE_PATH}")
else:
    logger.info(f"Clasificador de rostros cargado desde {FACE_CASCADE_PATH}")

if eye_cascade.empty():
    logger.warning(f"Clasificador de ojos no disponible desde {EYE_CASCADE_PATH}")


def aumentar_datos(cara):
    if cara.shape[0] == 0 or cara.shape[1] == 0:
        return [cara]

    filas, cols = cara.shape
    center = (cols // 2, filas // 2)
    M_pos = cv2.getRotationMatrix2D(center, 5, 1)
    M_neg = cv2.getRotationMatrix2D(center, -5, 1)

    variantes = [
        cara,
        cv2.convertScaleAbs(cara, alpha=1.1, beta=0),
        cv2.convertScaleAbs(cara, alpha=0.9, beta=0),
        cv2.warpAffine(cara, M_pos, (cols, filas)),
        cv2.warpAffine(cara, M_neg, (cols, filas)),
        cv2.convertScaleAbs(cara, alpha=1.2, beta=0),
    ]
    return variantes


def entrenar_modelo():
    faces_dir = current_app.config["FACES_DIR"]
    if not os.path.exists(faces_dir):
        logger.error(f"No existe la carpeta de rostros: {faces_dir}")
        return False

    rostros = []
    labels = []
    label_map = {}
    label_id = 0

    for persona in sorted(os.listdir(faces_dir)):
        persona_dir = os.path.join(faces_dir, persona)
        if not os.path.isdir(persona_dir):
            continue

        fotos = [f for f in os.listdir(persona_dir) if f.endswith(".jpg")]
        if not fotos:
            continue

        label_map[label_id] = persona
        logger.info(f"Entrenando: {persona} ({len(fotos)} fotos)")

        for foto in fotos:
            ruta = os.path.join(persona_dir, foto)
            try:
                img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                img = cv2.resize(img, (200, 200))
                variantes = aumentar_datos(img)
                for variante in variantes:
                    rostros.append(variante)
                    labels.append(label_id)
            except Exception as e:
                logger.error(f"Error procesando {foto}: {e}")

        label_id += 1

    if not rostros:
        logger.error("No se encontraron rostros para entrenar")
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(rostros, np.array(labels))

    model_path = os.path.join(faces_dir, "..", "modelo_lbph.yml")
    labels_path = os.path.join(faces_dir, "..", "labels.txt")

    recognizer.save(model_path)

    with open(labels_path, "w", encoding="utf-8") as f:
        for label_id, name in label_map.items():
            f.write(f"{label_id},{name}\n")

    logger.info(
        f"Modelo entrenado: {len(rostros)} imagenes, {len(label_map)} personas"
    )
    return True


def cargar_modelo():
    faces_dir = current_app.config["FACES_DIR"]
    model_path = os.path.join(faces_dir, "..", "modelo_lbph.yml")
    labels_path = os.path.join(faces_dir, "..", "labels.txt")

    if not os.path.exists(model_path) or not os.path.exists(labels_path):
        return None, {}

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)

    label_map = {}
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",", 1)
            if len(parts) == 2:
                label_map[int(parts[0])] = parts[1]

    return recognizer, label_map


def detectar_rostro(frame_gray):
    faces = face_cascade.detectMultiScale(
        frame_gray,
        scaleFactor=1.1,
        minNeighbors=3,
        minSize=(50, 50),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    logger.debug(f"Rostros detectados: {len(faces)}")
    return faces


def reconocer_rostro(frame_gray, recognizer, label_map):
    threshold = current_app.config["CONFIDENCE_THRESHOLD"]
    faces = detectar_rostro(frame_gray)

    results = []
    for x, y, w, h in faces:
        cara = frame_gray[y : y + h, x : x + w]
        cara = cv2.resize(cara, (200, 200))

        label, confidence = recognizer.predict(cara)
        percentage = 100 - confidence

        if confidence < threshold:
            name = label_map.get(label, "Desconocido")
            status = "recognized"
        elif confidence < 100:
            name = label_map.get(label, "Desconocido")
            status = "uncertain"
        else:
            name = "Desconocido"
            status = "unknown"

        results.append(
            {
                "name": name,
                "confidence": round(percentage, 2),
                "status": status,
                "bbox": [int(x), int(y), int(w), int(h)],
                "employee_name": name if status == "recognized" else None,
            }
        )

    return results


def guardar_rostro(frame_gray, employee_name, count):
    faces_dir = current_app.config["FACES_DIR"]
    persona_dir = os.path.join(faces_dir, employee_name)
    os.makedirs(persona_dir, exist_ok=True)

    logger.info(f"Intentando detectar rostro en imagen de {frame_gray.shape}")

    faces = detectar_rostro(frame_gray)
    if len(faces) == 0:
        logger.warning("No se detectó ningún rostro en la imagen")
        return None

    x, y, w, h = faces[0]
    logger.info(f"Rostro detectado en posición: x={x}, y={y}, w={w}, h={h}")

    cara = frame_gray[y : y + h, x : x + w]
    cara = cv2.resize(cara, (200, 200))

    filename = f"cara_{count:03d}.jpg"
    filepath = os.path.join(persona_dir, filename)
    cv2.imwrite(filepath, cara)

    logger.info(f"Rostro guardado: {filepath}")
    return filepath
