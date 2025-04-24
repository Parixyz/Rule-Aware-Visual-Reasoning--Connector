# CoreScense: DSL for Hierarchical Object Reasoning with Visual Models

**CoreScense** is a domain-specific language (DSL) designed for hierarchical object detection and classification across complex scenes. It enables users to define logical rules over objects and their relationships, navigate through nested scenes, and interface with multiple visual models (segmentors and classifiers) in a unified, structured pipeline.

---

## Overview

CoreScense provides a structured system to:

- Define scenes and objects hierarchically  
  *(e.g., a `House` containing `Windows`, `Doors`, etc.)*
- Attach model-driven attribute detection  
  *(e.g., `type`, `color`, `style`) implemented as Python modules, not just weights)*
- Write logic-based rules for scene validation  
  *(e.g., count constraints, mismatch detection)*
- Seamlessly connect AI models to a reasoning engine via structured semi-code execution

---

## Features

- Custom DSL for describing scenes, sub-scenes, and validation logic
- Model-driven segmentation and classification using executable `.py` model definitions (not just `.pth` weights)
- Logical rule engine supporting `forall`, `count`, `exists`, and nested conditions
- Executable pipeline turning DSL + image inputs into contradiction reports
- Hierarchical object modeling (scenes with embedded sub-scenes)
- DSL-to-model binding through a configuration file

---

## Concept: From Image to Validated Scene

A **scene** represents a root image containing multiple objects. Each object can have attributes such as `color`, `type`, and `style`, inferred using Python-based model modules. Scenes can also contain nested scenes (e.g., `Sky.FullScene`, `House.FullScene`).

---

## Example 1: Scene + Rules DSL

```dsl
Sky: {
  color: "sunset_orange"
  style: "vibrant"
  FullScene: {
    Scene: [Cloud*, Bird?]
  }
}

House: {
  color: "blue"
  FullScene: {
    Scene: [Roof, Window+, Door+, Chimney?]
  }
}

MainScene: {
  Scene: [Sky, House+]
  mood: "evening"
  temperature: 21.0
}

RULE R1:
  forall s in MainScene:
    if (s.type = "Sky" and s.color != "sunset_orange") then
      Contradict Code 10

Run: Find and Suggest (rules = [R1], scene = MainScene, output = "results.cfs")
```

---

## Required Components

### 1. Image Input
- A scene image that contains all relevant objects.

### 2. Model Configuration (`models_config.json`)

```json
{
  "Models": [
    {
      "name": "StyleClassifier",
      "type": "Classifier",
      "attribute": "style",
      "path": "models/style_class.py",
      "input_type": "CroppedObject"
    }
  ]
}
```

### 3. Visual Models
- **Segmentors**: detect objects and return masks or bounding boxes (e.g., `InstanceSegmentor` class)
- **Classifiers**: infer attributes such as `style`, `color`, `type` (e.g., `ClassifierAttr` class)

> Each model is implemented as a Python module exposing a callable interface (e.g., `__call__(image) -> str`) returning the predicted string attribute.

### 4. DSL Scene File (`example.dsl`)
- Describes the structure of the scene and defines the validation rules

### 5. Execution Script (`execute.py`)
- Parses the DSL, loads model Python classes, runs inference, validates rules

---

## Output

- Contradiction report saved as a `.cfs` file
- Optional: visual overlays, logs, model outputs

---

## Future Directions

- Scene visualizer with contradiction highlights
- Rule suggestion and learning from annotated examples
- Probabilistic/fuzzy rule support
- Web-based GUI for scene and rule authoring

 

