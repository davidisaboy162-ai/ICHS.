"""
ICHS API Server
FastAPI application for crop disease diagnosis
"""

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from ..ml.models import ImageModel, TextModel
from ..ml.data_processor import DataProcessor

app = FastAPI(title="ICHS API", version="0.1.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

# Initialize models
image_model = ImageModel()
text_model = TextModel()
data_processor = DataProcessor()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "ICHS API is running", "status": "healthy"}

@app.post("/predict/image")
async def predict_from_image(file: UploadFile = File(...)):
    """
    Predict crop disease from uploaded image

    Args:
        file: Image file upload

    Returns:
        Prediction results with confidence scores
    """
    try:
        # Read image file
        image_data = await file.read()

        # Preprocess image
        processed_image = data_processor.preprocess_image(image_data)

        # Make prediction
        prediction = image_model.predict(processed_image)

        return {
            "prediction": prediction,
            "model_type": "image",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Image prediction error: {str(e)}")
        return {"error": str(e), "status": "failed"}

@app.post("/predict/text")
async def predict_from_text(symptoms: str = Form(...)):
    """
    Predict crop disease from symptom description

    Args:
        symptoms: Text description of symptoms

    Returns:
        Prediction results with confidence scores
    """
    try:
        # Preprocess text
        processed_text = data_processor.preprocess_text(symptoms)

        # Make prediction
        prediction = text_model.predict(processed_text)

        return {
            "prediction": prediction,
            "model_type": "text",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Text prediction error: {str(e)}")
        return {"error": str(e), "status": "failed"}

@app.post("/predict/combined")
async def predict_combined(
    file: UploadFile = File(...),
    symptoms: str = Form(...)
):
    """
    Combined prediction using both image and text

    Args:
        file: Image file upload
        symptoms: Text description of symptoms

    Returns:
        Combined prediction results
    """
    try:
        # Process image
        image_data = await file.read()
        processed_image = data_processor.preprocess_image(image_data)

        # Process text
        processed_text = data_processor.preprocess_text(symptoms)

        # Get predictions
        image_pred = image_model.predict(processed_image)
        text_pred = text_model.predict(processed_text)

        # Combine predictions (simple averaging for now)
        combined_pred = {
            "image_prediction": image_pred,
            "text_prediction": text_pred,
            "combined_confidence": (image_pred.get("confidence", 0) + text_pred.get("confidence", 0)) / 2
        }

        return {
            "prediction": combined_pred,
            "model_type": "combined",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Combined prediction error: {str(e)}")
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
