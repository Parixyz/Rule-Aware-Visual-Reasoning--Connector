import random
from typing import Dict, List, Tuple, Optional
from PIL import Image as PILImage
from lark import Tree, Token
from collections import defaultdict
from models.Query import load_model_registry, query

class ObjectType:
    def __init__(self, name: str, attributes: List[str], ObjectList: List[Tuple[str, str]]):
        self.name = name
        self.attributes = attributes
        self.ObjectList = ObjectList

    def get_count_by_multiplicity(self, mult: str) -> int:
        return {
            "+": random.randint(1, 3),
            "*": random.randint(0, 3),
            "?": random.randint(0, 1)
        }.get(mult, 1)

class SceneObject:
    def __init__(self,typeId, type_name: str, source_image: Optional[PILImage.Image] = None, model_registry=None):
        self.type = type_name
        self.attributes: Dict[str, Optional[str]] = {}
        self.ObjectList: Dict[str, List['SceneObject']] = {}
        self.source_image: Optional[PILImage.Image] = source_image
        self.model_registry = model_registry or load_model_registry()

    def setup(self, obj_type: ObjectType):
        for attr in obj_type.attributes:
            self.attributes[attr] = None
        for child_name, _ in obj_type.ObjectList:
            self.ObjectList[child_name] = []

    def add_object(self, obj: 'SceneObject'):
        if obj.type not in self.ObjectList:
            self.ObjectList[obj.type] = []
        self.ObjectList[obj.type].append(obj)

    def get(self, key: str):
        if key in self.attributes:
            if self.attributes[key] is None and self.source_image:
                result = query(self.source_image, key, self.model_registry)
                self.attributes[key] = result
            return self.attributes[key]

        if self.source_image:
            children = query(self.source_image, key, self.model_registry)
            if isinstance(children, list):
                scene_objects = []
                for id, label_id, crop in children:
                    child = SceneObject(id,label_id, source_image=crop, model_registry=self.model_registry)
                    scene_objects.append(child)
                self.ObjectList[key] = scene_objects
                return scene_objects

        return None

    def find_all(self, type_name: str) -> List['SceneObject']:
        results = []
        if self.type == type_name:
            results.append(self)
        for lst in self.ObjectList.values():
            for child in lst:
                results.extend(child.find_all(type_name))
        return results

    def __str__(self, indent: int = 0) -> str:
        pad = "  " * indent
        out = f"{pad}{self.type} {{" + ", ".join(f"{k}={v}" for k, v in self.attributes.items()) + "}\n"
        for key in self.ObjectList:
            for child in self.ObjectList[key]:
                out += child.__str__(indent + 1)
        return out

def extract_object_types(tree: Tree):
    types = []
    for stmt in tree.find_data("type_def"):
        type_name = stmt.children[0].value
        attributes = []
        children = []
        for part in stmt.find_data("attr_block"):
            for attr_list in part.find_data("attr_list"):
                attributes = [c.value for c in attr_list.children if isinstance(c, Token)]
        for part in stmt.find_data("obj_block"):
            for item in stmt.find_data("obj_item"):
                child_name = item.children[0].value
                multiplicity = ''
                if len(item.children) > 1 and item.children[1].children:
                    multiplicity = item.children[1].children[0].value
                children.append((child_name, multiplicity))
        types.append(ObjectType(type_name, attributes, children))
    return types

def make_hierarchy(root_type_name, type_map, image=None):
    tdef = type_map[root_type_name]
    obj = SceneObject(tdef.name, "",source_image=image)
    obj.setup(tdef)
    return obj
