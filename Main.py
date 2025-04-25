from lark import Lark
from collections import defaultdict
from PIL import Image as PILImage
from Core.SceneObject import extract_object_types, make_hierarchy
from typing import Union


def get_parser():
    with open('grammar.lark', 'r') as f:
        grammar_text = f.read()
    return Lark(grammar_text, start="start", parser="lalr")



def FindContradictions(rules, root):
    for rule in rules:
        result = rule(root)
        if result:
            print(result)





def Parse(example_dsl):
    parser = get_parser()
    tree = parser.parse(example_dsl)
    return tree
type_map = None
def printTypes(tree):
    global type_map
    print("\n=== TYPES ===")
    types = extract_object_types(tree)
    for t in types:
        print({"name": t.name, "attributes": t.attributes, "children": t.ObjectList})
    type_map = {t.name: t for t in types}
    return 

#This part is Usually Generated
def Rule_SphereTorus_Limit(scene):
    spheres = scene.get("sphere")
    toruses = scene.get("torus")
    cubes = scene.get("cube")

    if spheres is None or toruses is None or cubes is None:
        return None  # or an informative message if you want

    if len(spheres) + len(toruses) > len(cubes):
        return "Contradiction: Too many spheres and toruses compared to cubes"

    return None

example_dsl = """
    type SimpleShape {
      attributes: [shape, mat]
      objects: []
    }

    type MainScene {
      attributes: []
      objects: [SimpleShape*]
    }
"""
tree = Parse(example_dsl)
printTypes(tree)
#End Gen

img_path = "C:/VLNLP/Test/D7K/COCO/images/scene_00095_angle_0.png"
image = PILImage.open(img_path).convert("RGB")

root = make_hierarchy("MainScene", type_map,image)

rules = [Rule_SphereTorus_Limit]
FindContradictions(rules, root)
