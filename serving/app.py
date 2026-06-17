import logging
import os

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from google.cloud import storage
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

def download_gcs_file(gcs_uri: str, local_path: str) -> None:
    parsed = urlparse(gcs_uri)
    bucket_name = parsed.netloc
    blob_name = parsed.path.lstrip("/")

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)


AIP_STORAGE_URI = os.getenv("AIP_STORAGE_URI")
MODEL_PATH = os.getenv("MODEL_PATH")

if AIP_STORAGE_URI:
    gcs_model_uri = AIP_STORAGE_URI.rstrip("/") + "/model.joblib"
    model_path = "/tmp/model.joblib"

    logger.info(f"Downloading model from {gcs_model_uri} to {model_path}")
    download_gcs_file(gcs_model_uri, model_path)

elif MODEL_PATH:
    model_path = MODEL_PATH
else:
    raise ValueError("No model location configured. Set AIP_STORAGE_URI or MODEL_PATH.")

logger.info(f"Loading model from: {model_path}")
model = joblib.load(model_path)

app = FastAPI()
model = joblib.load(model_path)


class PredictionRequest(BaseModel):
    instances: list[dict]


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/predict")
def predict(request: PredictionRequest):
    df = pd.DataFrame(request.instances)

    if "company" in df.columns:
        logger.info("Removing company column.")
        df = df.drop(columns=["company"])

    predictions = model.predict(df).tolist()
    probabilities = model.predict_proba(df)[:, 1].tolist()

    return {
        "predictions": [
            {
                "class": int(pred),
                "probability_cancelled": float(prob),
            }
            for pred, prob in zip(predictions, probabilities)
        ]
    }