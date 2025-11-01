# archivo: api.py
import os
import random
from typing import List, Dict, Tuple

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# =========================================================
# Config
# =========================================================
# Si más adelante quieres usar el modelo real, exporta USE_MOCK=0
USE_MOCK = os.getenv("USE_MOCK", "1") == "1"

# Clases por defecto (coinciden con el frontend)
DEFAULT_CLASSES: List[str] = [
    "healthy", "leaf_rust", "american_leaf_spot", "miner", "phoma"
]

# Cache global (evita recargar modelo en cada request)
MODEL = None
CLASSES = DEFAULT_CLASSES

app = FastAPI(title="CoffeeCare API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# Helpers
# =========================================================
def _load_real_model() -> Tuple[object, List[str]]:
    """
    Carga perezosa del modelo real desde tu paquete del proyecto.
    Si no existe la función/paquete, lanzará una excepción capturable por /health.
    """
    from coffeedd.interface.main import load_model  # <- tu función del proyecto
    model, class_names = load_model()
    return model, (class_names or DEFAULT_CLASSES)

# =========================================================
# Endpoints
# =========================================================
@app.get("/health")
def health_check():
    """
    Revisa si el modelo puede cargarse y está listo.
    - Si USE_MOCK=1, el servicio se considera 'healthy' sin cargar modelo real.
    - Si USE_MOCK=0, intenta cargar el modelo real y reporta el resultado.
    """
    global MODEL, CLASSES  # <--- DECLARAR GLOBAL AL INICIO

    if USE_MOCK:
        # En modo mock no cargamos modelo real
        return {
            "status": "healthy",
            "model_loaded": False,
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
    Predicción mock (aleatoria). Si desactivas el mock (USE_MOCK=0) y
    ya tienes lógica de inferencia, puedes usar MODEL/CLASSES aquí.
    """
    # Leemos el archivo (no se usa en el mock)
    _ = await file.read()

    # MOCK: genera clase/probabilidad aleatoria
    classes = CLASSES or DEFAULT_CLASSES
    pred_class = random.choice(classes)
    prob = round(random.uniform(0.70, 0.99), 2)

    # Distribución "raw" simulada
    raw: Dict[str, float] = {c: round(random.uniform(0.01, 0.99), 3) for c in classes}

    return {
        "class_name": pred_class,
        "probability": prob,
        "raw": raw
    }
