import os
import json
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Union
from PIL import Image
import torch
import numpy as np
import matplotlib.pyplot as plt
from torchvision.transforms import Compose, Resize, ToTensor
from torchvision.models.detection import maskrcnn_resnet50_fpn





# === Abstract Base Classes ===
class Model(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def predict(self, image: Image.Image):
        pass

class Segmentor(Model):
    def __init__(self, name: str):
        super().__init__(name)

    @abstractmethod
    def can_segment(self, obj_name: str) -> bool:
        pass

    @abstractmethod
    def supported_objects(self) -> List[str]:
        """Return a list of objects this segmentor can segment."""
        pass

    @abstractmethod
    def predict(self, image: Image.Image) -> List[Tuple[Image.Image, Image.Image, str]]:
        pass

class Classifier(Model):
    def __init__(self, name: str):
        super().__init__(name)

    @abstractmethod
    def get_supported_attribute(self) -> str:
        pass

    @abstractmethod
    def predict(self, image: Image.Image) -> str:
        pass