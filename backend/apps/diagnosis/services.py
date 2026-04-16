from dataclasses import dataclass
from typing import Optional


@dataclass
class PredictionResult:
    disease_name: str
    confidence: float
    raw_outputs: dict


class DiagnosisEngine:
    """
    Placeholder model-serving layer.
    Replace internals with TensorFlow (EfficientNet-B4) and BERT checkpoints.
    """

    def predict_from_text(self, symptoms: str) -> PredictionResult:
        text = symptoms.lower()
        if "yellow" in text or "spot" in text:
            disease = "Leaf Spot"
            confidence = 0.82
        elif "wilt" in text:
            disease = "Bacterial Wilt"
            confidence = 0.78
        else:
            disease = "Healthy"
            confidence = 0.55
        return PredictionResult(
            disease_name=disease,
            confidence=confidence,
            raw_outputs={"symptom_tokens": len(symptoms.split())},
        )

    def predict_from_image(self, image_file) -> PredictionResult:
        filename = getattr(image_file, "name", "uploaded-image")
        disease = "Leaf Blight"
        confidence = 0.74
        return PredictionResult(
            disease_name=disease,
            confidence=confidence,
            raw_outputs={"source": filename, "model": "efficientnet_b4_stub"},
        )

    def predict_combined(self, symptoms: Optional[str], image_file) -> PredictionResult:
        text_pred = self.predict_from_text(symptoms or "") if symptoms else None
        image_pred = self.predict_from_image(image_file) if image_file else None

        if text_pred and image_pred:
            confidence = round((text_pred.confidence + image_pred.confidence) / 2, 4)
            disease = text_pred.disease_name if text_pred.confidence >= image_pred.confidence else image_pred.disease_name
            raw_outputs = {
                "text": text_pred.raw_outputs,
                "image": image_pred.raw_outputs,
                "fusion": "simple-average",
            }
        else:
            pred = text_pred or image_pred
            confidence = pred.confidence
            disease = pred.disease_name
            raw_outputs = pred.raw_outputs

        return PredictionResult(disease_name=disease, confidence=confidence, raw_outputs=raw_outputs)
