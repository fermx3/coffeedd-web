# archivo: api.py
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
