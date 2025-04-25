import os
import json
from typing import List, Union, Tuple
from importlib import import_module
from PIL import Image as PILImage
import matplotlib.pyplot as plt
from models.model import Model, Segmentor, Classifier

DevMode = True
OUTPUT_DIR = "C://VLNLP//Test//D7K//Language//models//Debug"

MODEL_REGISTRY_JSON = [
    {
        "module": "TorchMaskRCNNShapeWSegmentor",
        "class": "TorchMaskRCNNShapeWSegmentor",
        "ATTR": "",
        "TYPE": "SEGMENTOR",
        "OBJECTS": ["sphere", "cone", "cylinder", "torus", "cube"],
        "ObjectType": ["Object1"]
    },
    {
        "module": "TorchMaterialClassifier",
        "class": "TorchMaterialClassifier",
        "ATTR": "material",
        "TYPE": "CLASSIFIER",
        "OBJECTS": [],
        "ObjectType": []
    }
]

MODEL_LOOKUP = {entry["class"]: entry for entry in MODEL_REGISTRY_JSON}

def load_model_registry() -> List[Model]:
    registry = []
    for model_info in MODEL_REGISTRY_JSON:
        module_name = f"models.{model_info['module']}"
        class_name = model_info["class"]
        model_class = getattr(import_module(module_name), class_name)
        registry.append(model_class())
    return registry

def ensure_model_for(query_key: str, registry: List[Model]) -> List[Model]:
    for model_info in MODEL_REGISTRY_JSON:
        if query_key in model_info.get("OBJECTS", []) or \
           query_key in model_info.get("ObjectType", []) or \
           query_key.lower() == model_info.get("ATTR", "").lower():
            class_name = model_info["class"]
            if not any(m.__class__.__name__ == class_name for m in registry):
                module_name = f"models.{model_info['module']}"
                model_class = getattr(import_module(module_name), class_name)
                instance = model_class()
                registry.append(instance)
                print(f"[INFO] Dynamically loaded: {class_name} for {query_key}")
    return registry

import os
import json
from typing import List, Union, Tuple
from importlib import import_module
from PIL import Image as PILImage
import matplotlib.pyplot as plt
from models.model import Model, Segmentor, Classifier

DevMode = True
OUTPUT_DIR = "C://VLNLP//Test//D7K//Language//models//Debug"

MODEL_REGISTRY_JSON = [
    {
        "module": "TorchMaskRCNNShapeWSegmentor",
        "class": "TorchMaskRCNNShapeWSegmentor",
        "ATTR": "",
        "TYPE": "SEGMENTOR",
        "OBJECTS": ["sphere", "cone", "cylinder", "torus", "cube"],
        "ObjectType": ["Object1"]
    },
    {
        "module": "TorchMaterialClassifier",
        "class": "TorchMaterialClassifier",
        "ATTR": "material",
        "TYPE": "CLASSIFIER",
        "OBJECTS": [],
        "ObjectType": []
    }
]

MODEL_LOOKUP = {entry["class"]: entry for entry in MODEL_REGISTRY_JSON}

def load_model_registry() -> List[Model]:
    registry = []
    for model_info in MODEL_REGISTRY_JSON:
        module_name = f"models.{model_info['module']}"
        class_name = model_info["class"]
        model_class = getattr(import_module(module_name), class_name)
        registry.append(model_class())
    return registry

def ensure_model_for(query_key: str, registry: List[Model]) -> List[Model]:
    for model_info in MODEL_REGISTRY_JSON:
        if query_key in model_info.get("OBJECTS", []) or query_key.lower() == model_info.get("ATTR", "").lower():
            class_name = model_info["class"]
            if not any(m.__class__.__name__ == class_name for m in registry):
                module_name = f"models.{model_info['module']}"
                model_class = getattr(import_module(module_name), class_name)
                instance = model_class()
                registry.append(instance)
                print(f"[INFO] Dynamically loaded: {class_name} for {query_key}")
    return registry

def query(image: PILImage.Image, query_key: str, registry: List[Model]) -> Union[str, List[Tuple[str, str, PILImage.Image]]]:
    registry = ensure_model_for(query_key, registry)

    for model in registry:
        model_info = MODEL_LOOKUP.get(model.__class__.__name__, {})
        model_type = model_info.get("TYPE", "")

        if model_type == "SEGMENTOR":
            detections = model.predict(image)
            object_type = model_info["ObjectType"][0] if model_info["ObjectType"] else ""

            if query_key in model_info.get("OBJECTS", []):
                # Filter
                filtered = [
                    (object_type, label, crop)
                    for crop, _, label in detections if label.lower() == query_key.lower()
                ]
                return filtered if filtered else f"No objects of type {query_key} found."

            elif query_key in model_info.get("ObjectType", []):
                # Return all 
                return [(object_type, label, crop) for crop, _, label in detections]

        if model_type == "CLASSIFIER" and query_key.lower() == model_info.get("ATTR", "").lower():
            return model.predict(image)

    return f"No model found that can handle: {query_key}"
