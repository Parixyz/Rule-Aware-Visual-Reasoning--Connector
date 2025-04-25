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
from models.model import Model, Segmentor, Classifier

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 64
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
transform = Compose([Resize((IMG_SIZE, IMG_SIZE)), ToTensor()])


class TorchMaterialClassifier(Classifier):
    MATERIAL_CLASSES = ["opaque", "transparent", "transparent_blue", "mirror", "gold"]

    def __init__(self):
        super().__init__("TorchMaterialClassifier")
        path = "C:/VLNLP/Test/D7K/COCO/material_classifier.pth"

        class MaterialNet(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.net = torch.nn.Sequential(
                    torch.nn.Flatten(),
                    torch.nn.Linear(3 * IMG_SIZE * IMG_SIZE, 256),
                    torch.nn.ReLU(),
                    torch.nn.Linear(256, len(TorchMaterialClassifier.MATERIAL_CLASSES))
                )
            def forward(self, x):
                return self.net(x)

        self.full_model = MaterialNet()
        state_dict = torch.load(path, map_location=device)
        self.full_model.load_state_dict(state_dict)
        self.full_model.to(device).eval()

    def get_supported_attribute(self) -> str:
        return "material"

    def predict(self, image: Image.Image) -> str:
        tensor = transform(image).unsqueeze(0).to(device)
        with torch.no_grad():
            pred = self.full_model(tensor)
        return self.MATERIAL_CLASSES[pred.argmax().item()]
