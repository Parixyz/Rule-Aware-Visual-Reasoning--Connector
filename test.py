from lark import Lark, Tree, Token
import random

class ObjectType:
    def __init__(self, name, attributes, ObjectList):
        self.name = name
        self.attributes = attributes
        self.ObjectList = ObjectList

    def get_count_by_multiplicity(self, mult):
        return {
            "+": random.randint(1, 3),
            "*": random.randint(0, 3),
            "?": random.randint(0, 1)
        }.get(mult, 1)

class SceneObject:
    def __init__(self, type_name):
        self.type = type_name
        self.attributes = {}
        self.ObjectList = {}

    def setup(self, obj_type):
        for attr in obj_type.attributes:
            self.attributes[attr] = None
        for child_name, _ in obj_type.ObjectList:
            self.ObjectList[child_name] = []

    def add_object(self, obj):
        if obj.type not in self.ObjectList:
            self.ObjectList[obj.type] = []
        self.ObjectList[obj.type].append(obj)

    def get(self, key):
        if key in self.attributes:
            return self.attributes[key]
        elif key in self.ObjectList:
            return self.ObjectList[key]
        return None

    def find_all(self, type_name):
        results = []
        if self.type == type_name:
            results.append(self)
        for lst in self.ObjectList.values():
            for child in lst:
                results.extend(child.find_all(type_name))
        return results

    def __str__(self, indent=0):
        pad = "  " * indent
        out = f"{pad}{self.type} {{" + ", ".join(f"{k}={v}" for k, v in self.attributes.items()) + "}\n"
        for key in self.ObjectList:
            for child in self.ObjectList[key]:
                out += child.__str__(indent + 1)
        return out

# === Extractors ===
def extract_object_types(tree):
    types = []
    for stmt in tree.find_data("type_def"):
        type_name = stmt.children[0].value
        attributes = []
        children = []
        for part in stmt.find_data("attr_block"):
            for attr_list in part.find_data("attr_list"):
                attributes = [c.value for c in attr_list.children if isinstance(c, Token)]
        for part in stmt.find_data("obj_block"):
            for item in part.find_data("obj_item"):
                child_name = item.children[0].value
                multiplicity = ''
                if len(item.children) > 1 and item.children[1].children:
                    multiplicity = item.children[1].children[0].value
                children.append((child_name, multiplicity))
        types.append(ObjectType(type_name, attributes, children))
    return types

# === Scene Constructor ===
def make_hierarchy(root_type_name, type_map):
    def build(type_name, depth=0):
        if type_name not in type_map:
            return None
        tdef = type_map[type_name]
        obj = SceneObject(tdef.name)
        obj.setup(tdef)
        if depth < 3:
            for child_name, multiplicity in tdef.ObjectList:
                count = tdef.get_count_by_multiplicity(multiplicity)
                for _ in range(count):
                    child = build(child_name, depth + 1)
                    if child:
                        obj.add_object(child)
        return obj

    return build(root_type_name)

# === Rule Function ===
def ShapeCountLimit(scene):
    count = 0
    for o in scene.get("Object1"):
        if o.get("shape") == "sphere":
            count += 1
    if count >= 5:
        return "contradiction 102"
    return 

# === Main Execution ===
if __name__ == "__main__":
    with open('grammar.lark', 'r') as f:
        grammar_text = f.read()

    example_dsl = """
    type Object1 {
      attributes: [shape, mat]
      objects: []
    }

    type MainScene {
      attributes: [BackgroundColor]
      objects: [Object1*]
    }
    """

    parser = Lark(grammar_text, start="start", parser="lalr")
    tree = parser.parse(example_dsl)

    print("\n=== TYPES ===")
    types = extract_object_types(tree)
    for t in types:
        print({"name": t.name, "attributes": t.attributes, "children": t.ObjectList})

    type_map = {t.name: t for t in types}
    root = make_hierarchy("MainScene", type_map)

    print("\n=== GENERATED SCENE ===")
    print(root)

    print("\n=== RULE RESULTS ===")
    rules = [ShapeCountLimit]
    for rule in rules:
        result = rule(root)
        if result:
            print(result)
