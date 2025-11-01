# api.py — CoffeeCare API
import os
import io
import base64
import random
from typing import List, Dict, Tuple

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# =========================================================
# Configuración
# =========================================================
# Cuando tengas el modelo real, exporta USE_MOCK=0
USE_MOCK = os.getenv("USE_MOCK", "1") == "1"

# Tamaño máximo permitido (MB) para rechazar archivos muy grandes desde la API
MAX_FILE_MB = float(os.getenv("MAX_FILE_MB", "8"))

# Clases por defecto (coinciden con el frontend)
DEFAULT_CLASSES: List[str] = [
    "healthy", "leaf_rust", "american_leaf_spot", "miner", "phoma"
]

# Cache global del modelo real (si se usa)
MODEL = None
CLASSES = DEFAULT_CLASSES

app = FastAPI(title="CoffeeCare API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # ajusta si necesitas restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Helpers
# =========================================================
def _load_real_model() -> Tuple[object, List[str]]:
    """
    CARGA PEREZOSA DEL MODELO REAL
    -----------------------------------------------------
    ➜ REEMPLAZA esta importación por la de tu proyecto.
       Debe devolver (model, class_names)
    """
    from coffeedd.interface.main import load_model  # <-- PUNTO DE ENCHUFE
    model, class_names = load_model()
    return model, (class_names or DEFAULT_CLASSES)


def _to_base64(pil_image) -> str:
    """Codifica una PIL.Image a base64 (PNG). Útil si quieres devolver overlays."""
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# =========================================================
# Endpoints
# =========================================================
@app.get("/health")
def health_check():
    """
    Estado del servicio/modelo.
    - Modo MOCK (USE_MOCK=1): responde healthy sin cargar el modelo real.
    - Modo REAL (USE_MOCK=0): intenta cargar el modelo y reporta estado.
    """
    global MODEL, CLASSES

    if USE_MOCK:
        return {
            "status": "healthy",
            "model_loaded": False,   # no se carga el modelo real en mock
            "use_mock": True
        }

    try:
        if MODEL is None:
            MODEL, CLASSES = _load_real_model()
        return {
            "status": "healthy",
            "model_loaded": MODEL is not None,
            "use_mock": False
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "model_loaded": False,
            "use_mock": False,
            "error": str(e)
        }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Predicción:
    - En modo MOCK genera resultados aleatorios con probabilidad ∈ [0.70, 0.99].
    - En modo REAL usa MODEL/CLASSES y devuelve:
        {
          "class_name": str,
          "probability": float (0..1),
          "raw": {clase: score, ...}  ó  lista de scores,
          "image_base64": str (opcional)
        }
    """
    # Validación de tamaño
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande: {size_mb:.2f} MB (máximo {MAX_FILE_MB:.0f} MB)."
        )

    # =========== MODO MOCK ===========
    if USE_MOCK:
        classes = CLASSES or DEFAULT_CLASSES
        pred_class = random.choice(classes)
        prob = round(random.uniform(0.70, 0.99), 2)  # fracción (0.70 → 70%)
        raw: Dict[str, float] = {c: round(random.uniform(0.01, 0.99), 3) for c in classes}

        return {
            "class_name": pred_class,
            "probability": float(prob),  # el frontend muestra prob*100
            "raw": raw
            # "image_base64": _to_base64(overlay_pil)  # opcional si quieres mostrar overlay
        }

    # =========== MODO REAL ===========
    try:
        # 1) Cargar modelo si aún no está en memoria
        global MODEL, CLASSES
        if MODEL is None:
            MODEL, CLASSES = _load_real_model()

        # 2) Preprocesar la imagen (PUNTO DE ENCHUFE)
        #    - convierte 'content' (bytes) a PIL/numpy y aplica tus transforms
        # from PIL import Image
        # import numpy as np
        # pil_img = Image.open(io.BytesIO(content)).convert("RGB")
        # x = preprocess(pil_img)  # <-- tu función

        # 3) Inferencia (PUNTO DE ENCHUFE)
        # scores = MODEL.predict(x)              # <-- tu llamada
        # probas = softmax(scores)               # lista/np.array con probs
        # idx = int(np.argmax(probas))
        # pred_class = CLASSES[idx]
        # prob = float(probas[idx])              # 0..1

        # 4) Si quieres devolver un overlay/gradcam (PUNTO DE ENCHUFE)
        # overlay = make_overlay(pil_img, MODEL, idx)  # opcional
        # img_b64 = _to_base64(overlay)

        # --------- DEMO de forma REAL (a falta de tu lógica) ---------
        pred_class = CLASSES[0]
        prob = 0.85
        raw = {c: (0.85 if c == pred_class else 0.03) for c in CLASSES}
        # img_b64 = _to_base64(pil_img)  # por ejemplo el input mismo

        return {
            "class_name": pred_class,
            "probability": prob,
            "raw": raw
            # , "image_base64": img_b64
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inferencia falló: {e}")


# =========================================================
# Ejecución local
# =========================================================
# Ejecuta así:
#   USE_MOCK=1 uvicorn api:app --reload --host 0.0.0.0 --port 8000
# Cuando tengas el modelo real:
#   USE_MOCK=0 uvicorn api:app --reload --host 0.0.0.0 --port 8000
