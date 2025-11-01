# archivo: api.py
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import random
from pydantic import BaseModel
import asyncio

# Configuración global (mock)
MODEL_ENABLED = True
RESPONSE_DELAY = 2.0 # segundos
SIMULATE_ERROR = False

#Simular modelos de respuesta
class HealthResponse(BaseModel):
    status: str
    model_loaded: bool = None
    error: str = None

class ConfigRequest(BaseModel):
    model_enabled: bool = None
    response_delay: float = None
    simulate_error: bool = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint de health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the model is loaded and ready (MOCK VERSION)"""

    # Simular delay de procesamiento
    await asyncio.sleep(RESPONSE_DELAY)

    try:
        # Simular el intento de cargar el modelo
        if not MODEL_ENABLED:
            raise Exception("Model loading is disabled")

        if SIMULATE_ERROR:
            raise Exception("coffeedd.interface.main module not found - this is a mock API")

        # Si llegamos aquí, simular que el modelo se cargó correctamente
        return HealthResponse(
            status="healthy",
            model_loaded=True
        )

    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            error=str(e)
        )

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Mock: genera clase aleatoria
    classes = ["healthy", "leaf_rust", "american_leaf_spot", "miner", "phoma"]
    pred_class = random.choice(classes)
    prob = round(random.uniform(0.7, 0.99), 2)
    return {
        "class_name": pred_class,
        "probability": prob,
        "raw": [random.random() for _ in classes]
    }
