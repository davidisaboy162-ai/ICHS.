from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageOps, ImageStat

try:
    import tensorflow as tf
except Exception:  # pragma: no cover - tensorflow is optional at import time
    tf = None


@dataclass
class PredictionResult:
    disease_name: str
    confidence: float
    raw_outputs: dict


class DiagnosisEngine:
    """
    Hybrid inference layer.

    It loads a trained CNN if `models/plantvillage_efficientnetb4_final.keras` exists.
    Otherwise it falls back to deterministic heuristics so the app still works
    before training is complete.
    """

    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.model_path = self.repo_root / "models" / "plantvillage_efficientnetb4_final.keras"
        self.label_map_path = self.repo_root / "models" / "label_map.json"
        self.model = None
        self.label_names = []
        self.input_size = 224
        self._load_model_if_available()

    def _load_model_if_available(self) -> None:
        if tf is None or not self.model_path.exists():
            return

        try:
            self.model = tf.keras.models.load_model(self.model_path)
            input_shape = self.model.input_shape
            if isinstance(input_shape, list):
                input_shape = input_shape[0]
            self.input_size = int(input_shape[1] or 224)
            if self.label_map_path.exists():
                import json

                with open(self.label_map_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                self.label_names = payload.get("labels", [])
        except Exception:
            self.model = None
            self.label_names = []

    def _load_image(self, image_file) -> Image.Image:
        if hasattr(image_file, "read"):
            raw = image_file.read()
            if hasattr(image_file, "seek"):
                image_file.seek(0)
            image = Image.open(BytesIO(raw))
        if isinstance(image_file, (str, Path)):
            image = Image.open(image_file)
        else:
            if not hasattr(image_file, "read"):
                raise ValueError("Unsupported image input")

        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")

    def _prepare_image(self, image_file, size: int) -> Image.Image:
        image = self._load_image(image_file)
        # Keep the subject centered while matching the model's square input shape.
        return ImageOps.fit(
            image,
            (size, size),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

    def _heuristic_image_prediction(self, image_file) -> PredictionResult:
        image = self._prepare_image(image_file, 224)
        stats = ImageStat.Stat(image)
        mean_r, mean_g, mean_b = stats.mean[:3]
        saturation = float(np.mean(np.asarray(image.convert("HSV"))[:, :, 1])) / 255.0
        green_ratio = mean_g / max(mean_r + mean_b, 1)
        red_blue_gap = abs(mean_r - mean_b) / max(mean_r + mean_b, 1)
        brightness = sum(stats.mean[:3]) / 3

        if green_ratio > 0.48 and saturation > 0.16 and brightness > 60:
            disease = "Healthy"
            confidence = 0.74
        elif brightness < 55 or red_blue_gap > 0.28:
            disease = "Leaf Blight"
            confidence = 0.71
        elif saturation > 0.22 and green_ratio > 0.32:
            disease = "Leaf Spot"
            confidence = 0.69
        else:
            disease = "Disease Suspect"
            confidence = 0.66

        return PredictionResult(
            disease_name=disease,
            confidence=confidence,
            raw_outputs={
                "mode": "heuristic-image",
                "green_ratio": round(float(green_ratio), 4),
                "saturation": round(float(saturation), 4),
                "red_blue_gap": round(float(red_blue_gap), 4),
                "brightness": round(float(brightness), 4),
            },
        )

    def _model_image_prediction(self, image_file) -> PredictionResult:
        image = self._prepare_image(image_file, self.input_size)
        arr = np.asarray(image, dtype=np.float32)[None, ...]
        if tf is None:
            return self._heuristic_image_prediction(image_file)

        variants = [arr, np.flip(arr, axis=2)]
        probs_list = []
        for variant in variants:
            normalized = tf.keras.applications.efficientnet.preprocess_input(variant.copy())
            probs_list.append(self.model.predict(normalized, verbose=0)[0])

        probs = np.mean(probs_list, axis=0)
        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])
        disease = self.label_names[top_idx] if self.label_names and top_idx < len(self.label_names) else f"Class {top_idx}"
        return PredictionResult(
            disease_name=disease,
            confidence=confidence,
            raw_outputs={
                "mode": "cnn",
                "top_index": top_idx,
                "top_probability": confidence,
                "tta": "horizontal-flip-ensemble",
            },
        )

    def predict_from_image(self, image_file) -> PredictionResult:
        if self.model is not None:
            return self._model_image_prediction(image_file)
        return self._heuristic_image_prediction(image_file)

    def predict_from_text(self, symptoms: str) -> PredictionResult:
        text = symptoms.lower()
        keyword_map = [
            (("yellow", "spot", "speck", "patch"), ("Leaf Spot", 0.83)),
            (("wilt", "droop", "collapse"), ("Bacterial Wilt", 0.8)),
            (("powder", "white", "fungal"), ("Powdery Mildew", 0.79)),
            (("blight", "brown", "necrotic"), ("Leaf Blight", 0.77)),
            (("mosaic", "curl", "mottled"), ("Mosaic Virus", 0.76)),
        ]

        for keywords, (disease, confidence) in keyword_map:
            if any(keyword in text for keyword in keywords):
                return PredictionResult(
                    disease_name=disease,
                    confidence=confidence,
                    raw_outputs={"mode": "rule-text", "matched_keywords": list(keywords)},
                )

        return PredictionResult(
            disease_name="Healthy",
            confidence=0.56,
            raw_outputs={"mode": "rule-text", "matched_keywords": []},
        )

    def predict_combined(self, symptoms: Optional[str], image_file) -> PredictionResult:
        text_pred = self.predict_from_text(symptoms or "") if symptoms else None
        image_pred = self.predict_from_image(image_file) if image_file else None

        if text_pred and image_pred:
            confidence = round((text_pred.confidence * 0.45) + (image_pred.confidence * 0.55), 4)
            disease = image_pred.disease_name if image_pred.confidence >= text_pred.confidence else text_pred.disease_name
            raw_outputs = {
                "text": text_pred.raw_outputs,
                "image": image_pred.raw_outputs,
                "fusion": "weighted-average",
            }
        else:
            pred = text_pred or image_pred
            confidence = pred.confidence
            disease = pred.disease_name
            raw_outputs = pred.raw_outputs

        return PredictionResult(disease_name=disease, confidence=confidence, raw_outputs=raw_outputs)
