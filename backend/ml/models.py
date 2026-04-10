"""Model definitions for ICHS"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseModel(ABC):
    @abstractmethod
    def build(self):
        pass
    
    @abstractmethod
    def train(self, X_train, y_train):
        pass
    
    @abstractmethod
    def predict(self, X):
        pass


class ImageModel(BaseModel):
    """CNN for image-based diagnosis"""
    
    def __init__(self, config=None):
        self.config = config or {}
        logger.info("ImageModel initialized")
    
    def build(self):
        pass
    
    def train(self, X_train, y_train):
        pass
    
    def predict(self, X):
        pass


class TextModel(BaseModel):
    """NLP for text-based diagnosis"""
    
    def __init__(self, config=None):
        self.config = config or {}
        logger.info("TextModel initialized")
    
    def build(self):
        pass
    
    def train(self, X_train, y_train):
        pass
    
    def predict(self, X):
        pass
