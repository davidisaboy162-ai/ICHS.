"""
Dataset Management Module
Handles dataset loading, preprocessing, and management for ICHS
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DatasetManager:
    """Manages datasets for ICHS project"""

    def __init__(self, base_path: str = "datasets"):
        """
        Initialize DatasetManager

        Args:
            base_path: Base path to datasets directory
        """
        self.base_path = Path(base_path)
        self.images_path = self.base_path / "images"
        self.text_path = self.base_path / "text"
        self.processed_path = self.base_path / "processed"

        # Create directories if they don't exist
        for path in [self.images_path, self.text_path, self.processed_path]:
            path.mkdir(parents=True, exist_ok=True)

        logger.info(f"DatasetManager initialized with base path: {base_path}")

    def load_image_dataset(self, dataset_name: str) -> Dict[str, List[str]]:
        """
        Load image dataset from directory structure

        Args:
            dataset_name: Name of the dataset folder

        Returns:
            Dictionary mapping class names to image paths
        """
        dataset_path = self.images_path / dataset_name
        if not dataset_path.exists():
            logger.warning(f"Dataset {dataset_name} not found")
            return {}

        class_images = {}
        for class_dir in dataset_path.iterdir():
            if class_dir.is_dir():
                class_name = class_dir.name
                images = [str(img) for img in class_dir.glob("*.jpg")]
                images.extend([str(img) for img in class_dir.glob("*.png")])
                images.extend([str(img) for img in class_dir.glob("*.jpeg")])
                class_images[class_name] = images
                logger.info(f"Found {len(images)} images for class {class_name}")

        return class_images

    def load_text_dataset(self, filename: str) -> pd.DataFrame:
        """
        Load text dataset from CSV file

        Args:
            filename: Name of the CSV file

        Returns:
            DataFrame with text data
        """
        file_path = self.text_path / filename
        if not file_path.exists():
            logger.warning(f"Text dataset {filename} not found")
            return pd.DataFrame()

        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded text dataset with {len(df)} samples")
            return df
        except Exception as e:
            logger.error(f"Error loading text dataset: {str(e)}")
            return pd.DataFrame()

    def save_processed_dataset(self, data: np.ndarray, labels: np.ndarray,
                             filename: str):
        """
        Save processed dataset

        Args:
            data: Processed data array
            labels: Labels array
            filename: Output filename
        """
        output_path = self.processed_path / filename
        np.savez(output_path, data=data, labels=labels)
        logger.info(f"Saved processed dataset to {output_path}")

    def load_processed_dataset(self, filename: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load processed dataset

        Args:
            filename: Dataset filename

        Returns:
            Tuple of (data, labels)
        """
        file_path = self.processed_path / filename
        if not file_path.exists():
            logger.warning(f"Processed dataset {filename} not found")
            return np.array([]), np.array([])

        try:
            loaded = np.load(file_path)
            logger.info(f"Loaded processed dataset from {file_path}")
            return loaded['data'], loaded['labels']
        except Exception as e:
            logger.error(f"Error loading processed dataset: {str(e)}")
            return np.array([]), np.array([])

    def get_dataset_stats(self) -> Dict:
        """
        Get statistics about available datasets

        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            "image_datasets": {},
            "text_datasets": [],
            "processed_datasets": []
        }

        # Image datasets
        if self.images_path.exists():
            for dataset_dir in self.images_path.iterdir():
                if dataset_dir.is_dir():
                    class_counts = {}
                    for class_dir in dataset_dir.iterdir():
                        if class_dir.is_dir():
                            count = len(list(class_dir.glob("*.jpg"))) + \
                                   len(list(class_dir.glob("*.png"))) + \
                                   len(list(class_dir.glob("*.jpeg")))
                            class_counts[class_dir.name] = count
                    stats["image_datasets"][dataset_dir.name] = class_counts

        # Text datasets
        if self.text_path.exists():
            stats["text_datasets"] = [f.name for f in self.text_path.glob("*.csv")]

        # Processed datasets
        if self.processed_path.exists():
            stats["processed_datasets"] = [f.name for f in self.processed_path.glob("*.npz")]

        return stats


if __name__ == "__main__":
    manager = DatasetManager()
    stats = manager.get_dataset_stats()
    print("Dataset Statistics:")
    print(stats)
