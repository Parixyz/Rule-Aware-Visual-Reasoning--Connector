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

class TorchMaskRCNNShapeWSegmentor(Segmentor):
    SHAPE_CLASSES = {
        1: "sphere",
        2: "cone",
        3: "cylinder",
        4: "torus",
        5: "cube"
    }

    def __init__(self):
        super().__init__("TorchMaskRCNNSegmentor")
        path = "C:/VLNLP/Test/D7K/COCO/mask_rcnn_model.pth"
        self.model = maskrcnn_resnet50_fpn(num_classes=len(self.SHAPE_CLASSES) + 1)
        self.model.load_state_dict(torch.load(path, map_location=device))
        self.model.to(device).eval()

    def can_segment(self, obj_name: str) -> bool:
        return obj_name.lower() in [x.lower() for x in self.SHAPE_CLASSES.values()]

    def predict(self, image: Image.Image) -> List[Tuple[Image.Image, Image.Image, str]]:
        image_tensor = ToTensor()(image).unsqueeze(0).to(device)
        with torch.no_grad():
            output = self.model(image_tensor)[0]
        results = []
        for box, mask, label, score in zip(output['boxes'], output['masks'], output['labels'], output['scores']):
            if score < 0.5:
                continue
            x1, y1, x2, y2 = map(int, box.tolist())
            crop = image.crop((x1, y1, x2, y2))
            mask_img = Image.fromarray((mask[0].cpu().numpy() > 0.5).astype(np.uint8) * 255)
            label_str = self.SHAPE_CLASSES.get(label.item(), "unknown")
            results.append((crop, mask_img, label_str))
        return results
    def supported_objects(self) -> List[str]:
        return ["sphere", "cone", "cylinder", "torus", "cube"]
