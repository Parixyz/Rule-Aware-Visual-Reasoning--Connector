# DSL Tree Extractor
from lark import Tree, Token
import random

class ObjectType:
    def __init__(self, name, attributes, ObjectList):
        self.name = name
        self.attributes = attributes
        self.ObjectList = ObjectList

    def random_instance(self, type_map, depth=0):
        obj = SceneObject(self.name)
        obj.setup(self)
        if depth < 3:
            for child_type, multiplicity in self.ObjectList:
                if child_type in type_map:
                    count = self.get_count_by_multiplicity(multiplicity)
                    for _ in range(count):
                        child = type_map[child_type].random_instance(type_map, depth + 1)
                        obj.add_object(child)
        return obj

    def random_value(self, attr):
        if attr == "shape":
            return random.choice(["sphere", "cube", "torus"])
        if attr == "mat":
            return random.choice(["gold", "silver", "wood"])
        if attr == "BackgroundColor":
            return random.choice(["blue", "gray", "green"])
        return f"val_{random.randint(0, 99)}"

    def get_count_by_multiplicity(self, mult):
        if mult == "+":
            return random.randint(1, 3)
        if mult == "*":
            return random.randint(0, 3)
        if mult == "?":
            return random.randint(0, 1)
        return 1

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

    def get(self, key):
        if key in self.attributes:
            return self.attributes[key]
        elif key in self.ObjectList:
            return self.ObjectList[key]
        return None

    def add_object(self, obj):
        if obj.type not in self.ObjectList:
            self.ObjectList[obj.type] = []
        self.ObjectList[obj.type].append(obj)

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

# Extractors

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
                if len(item.children) > 1 and isinstance(item.children[1], Tree):
                    if item.children[1].children:
                        multiplicity = item.children[1].children[0].value
                children.append((child_name, multiplicity))
        types.append(ObjectType(type_name, attributes, children))
    return types

def extract_scenes(tree):
    scenes = []
    for stmt in tree.find_data("scene_check"):
        scene_name = stmt.children[0].value
        folder_path = stmt.children[1].value.strip('"')
        root_type = stmt.children[2].value
        scenes.append({"name": scene_name, "path": folder_path, "root_type": root_type})
    return scenes

def extract_method_calls(tree):
    methods = []
    for stmt in tree.find_data("method_call"):
        caller = stmt.children[0].value
        rules = [c.value for c in stmt.children[3:] if isinstance(c, Token)]
        methods.append({"caller": caller, "rules": rules})
    return methods

if __name__ == "__main__":
    from lark import Lark

    grammar = """
    start: statement+
    statement: type_def | rule_def | scene_check | method_call
    type_def: "type" IDENT "{" type_body "}"
    type_body: attr_block obj_block
    attr_block: "attributes:" "[" attr_list? "]"
    attr_list: IDENT ("," IDENT)*
    obj_block: "objects:" "[" obj_list? "]"
    obj_list: obj_item ("," obj_item)*
    obj_item: IDENT multiplicity?
    multiplicity: "+" | "*" | "?"
    rule_def: "rule" IDENT "(" IDENT ":" IDENT ")" "{" rule_body "}"
    rule_body: (for_stmt | if_stmt)+
    for_stmt: "for" IDENT "in" IDENT "." IDENT "do" "{" if_stmt+ "}"
    if_stmt: "if" condition "then" "{" contradiction "}"
    condition: count_condition | expr
    count_condition: "count" "(" field ")" COMPARE value
    expr: IDENT "." IDENT COMPARE value
    field: IDENT ("." IDENT)*
    COMPARE: "=" | ">" | "<" | ">=" | "<=" | "!="
    value: STRING | NUMBER
    contradiction: "contradiction" NUMBER
    scene_check: IDENT "=" "LoadScene" "(" STRING "," IDENT ")"
    method_call: IDENT ".Check(" IDENT "," IDENT "," "[" IDENT ("," IDENT)* "]" ")"
    %import common.CNAME -> IDENT
    %import common.ESCAPED_STRING -> STRING
    %import common.NUMBER
    %import common.WS
    %ignore WS
    """

    example_dsl = """
    type Object1 {
      attributes: [shape, mat]
      objects: []
    }

    type MainScene {
      attributes: [BackgroundColor]
      objects: [Object1*]
    }

    rule ShapeCountLimit(scene: MainScene) {
      for o in scene.Object1 do {
        if count(scene.Object1.shape) >= 5 then {
          contradiction 102
        }
      }
    }

    rule SphereTorusVsCubes(scene: MainScene) {
      if count(scene.Object1.shape) > 10 then {
        contradiction 103
      }
    }

    scene1 = LoadScene("Folder path", MainScene)
    scene1.Check(start, end, [ShapeCountLimit, SphereTorusVsCubes])
    """

    parser = Lark(grammar, start="start", parser="lalr")
    tree = parser.parse(example_dsl)

    print("=== DSL PARSE TREE ===")
    print(tree.pretty())

    print("\n=== TYPES ===")
    types = extract_object_types(tree)
    for t in types:
        print({"name": t.name, "attributes": t.attributes, "children": t.ObjectList})

print("=== RULE STRINGS ===")
def rebuild_rule_as_string(rule_name, param_name, param_type, rule_body_tree):
    def extract_condition_string(condition_tree):
        if condition_tree.data == "count_condition":
            field = ".".join(token.value for token in condition_tree.children[0].children)
            op = condition_tree.children[1].value
            val = condition_tree.children[2].children[0].value
            return f"count({field}) {op} {val}"
        elif condition_tree.data == "expr":
            left = ".".join(token.value for token in condition_tree.children[:2])
            op = condition_tree.children[2].value
            val = condition_tree.children[3].children[0].value
            return f"{left} {op} {val}"
        return ""

    def extract_if_stmt(if_stmt):
        condition = extract_condition_string(if_stmt.children[0])
        contradiction_code = if_stmt.children[1].children[0].value
        return f"    if {condition} then {{\n      contradiction {contradiction_code}\n    }}"

    def extract_for_stmt(for_stmt):
        var = for_stmt.children[0].value
        container = for_stmt.children[1].value + "." + for_stmt.children[2].value
        body = "\n".join(extract_if_stmt(child) for child in for_stmt.find_data("if_stmt"))
        return f"  for {var} in {container} do {{\n{body}\n  }}"

    rule_lines = [f"rule {rule_name}({param_name}: {param_type}) {{"]
    for node in rule_body_tree.children:
        if isinstance(node, Tree):
            if node.data == "for_stmt":
                rule_lines.append(extract_for_stmt(node))
            elif node.data == "if_stmt":
                rule_lines.append(extract_if_stmt(node))
    rule_lines.append("}")
    return "\n".join(rule_lines)

x= (tree.find_data("rule_def"))
for stmt in tree.find_data("rule_def"):
    rule_name = stmt.children[0].value
    param_name = stmt.children[1].value
    param_type = stmt.children[2].value
    rule_body = stmt.children[3]
    print(rebuild_rule_as_string(rule_name, param_name, param_type, rule_body))
    print("-")
    


print("\n=== SCENES ===")
scenes = extract_scenes(tree)
for s in scenes:
  print(s)

print("\n=== METHOD CALLS ===")
methods = extract_method_calls(tree)
for m in methods:
  print(m)

def generate_python_methods(rules):
    python_methods = []
    for rule in rules:
        method_name = rule['name']
        param_name = rule['param']
        param_type = rule['type']
        rule_body = rule['body']
        
        python_code = f"def {method_name}({param_name}):\n"
        
        # Process the rule body
        if rule_body:
            for node in rule_body.children:
                if node.data == "for_stmt":
                    var = node.children[0].value
                    container = f"{node.children[1].value}_get_{node.children[2].value}"
                    container_py = f"{param_name}.get('{node.children[1].value}').get('{node.children[2].value}')"
                    
                    python_code += f"    for {var} in {container_py}:\n"
                    
                    # Process if statements inside for
                    for if_node in node.find_data("if_stmt"):
                        condition = if_node.children[0]
                        contradiction = if_node.children[1].children[0].value
                        
                        if condition.data == "count_condition":
                            field_parts = [t.value for t in condition.children[0].children]
                            op = condition.children[1].value
                            val = condition.children[2].children[0].value
                            
                            # Handle count conditions
                            if len(field_parts) == 2:  # e.g., scene.Object1
                                container_obj = f"{param_name}.get('{field_parts[0]}').get('{field_parts[1]}')"
                                python_code += f"        if len({container_obj}) {op} {val}:\n"
                            else:  # e.g., scene.Object1.shape
                                container_obj = f"{param_name}.get('{field_parts[0]}').get('{field_parts[1]}')"
                                attr = field_parts[2]
                                python_code += f"        if sum(1 for obj in {container_obj} if obj.attributes.get('{attr}')) {op} {val}:\n"
                            
                            python_code += f"            return 'contradiction {contradiction}'\n"
                            
                        elif condition.data == "expr":
                            left_parts = [t.value for t in condition.children[:2]]
                            op = condition.children[2].value
                            val = condition.children[3].children[0].value
                            
                            obj = f"{param_name}.get('{left_parts[0]}').get('{left_parts[1]}')"
                            python_code += f"        if {obj}.attributes.get('{left_parts[1]}') {op} {val}:\n"
                            python_code += f"            return 'contradiction {contradiction}'\n"
                
                elif node.data == "if_stmt":
                    condition = node.children[0]
                    contradiction = node.children[1].children[0].value
                    
                    if condition.data == "count_condition":
                        field_parts = [t.value for t in condition.children[0].children]
                        op = condition.children[1].value
                        val = condition.children[2].children[0].value
                        
                        if len(field_parts) == 2:  # e.g., scene.Object1
                            container_obj = f"{param_name}.get('{field_parts[0]}').get('{field_parts[1]}')"
                            python_code += f"    if len({container_obj}) {op} {val}:\n"
                        else:  # e.g., scene.Object1.shape
                            container_obj = f"{param_name}.get('{field_parts[0]}').get('{field_parts[1]}')"
                            attr = field_parts[2]
                            python_code += f"    if sum(1 for obj in {container_obj} if obj.attributes.get('{attr}')) {op} {val}:\n"
                        
                        python_code += f"        return 'contradiction {contradiction}'\n"
                    
                    elif condition.data == "expr":
                        left_parts = [t.value for t in condition.children[:2]]
                        op = condition.children[2].value
                        val = condition.children[3].children[0].value
                        
                        obj = f"{param_name}.get('{left_parts[0]}').get('{left_parts[1]}')"
                        python_code += f"    if {obj}.attributes.get('{left_parts[1]}') {op} {val}:\n"
                        python_code += f"        return 'contradiction {contradiction}'\n"
        
        python_code += "    return None\n\n"
        python_methods.append(python_code)
    
    return python_methods

# First, let's create a dictionary of rule strings
rule_strings = {}
for stmt in tree.find_data("rule_def"):
    rule_name = stmt.children[0].value
    rule_string = rebuild_rule_as_string(
        rule_name, 
        stmt.children[1].value, 
        stmt.children[2].value, 
        stmt.children[3]
    )
    rule_strings[rule_name] = rule_string

print("=== RULE STRINGS DICTIONARY ===")
for name, rule_str in rule_strings.items():
    print(f"{name}:\n{rule_str}\n")

# Now let's generate Python methods from these rule strings
def generate_python_methods_from_strings(rule_strings):
    python_methods = {}
    
    for rule_name, rule_str in rule_strings.items():
        # Parse the rule string to extract components
        lines = rule_str.split('\n')
        param_line = lines[0]
        param_name = param_line.split('(')[1].split(':')[0].strip()
        
        py_code = f"def {rule_name}({param_name}):\n"
        indent = "    "
        
        # Process each line of the rule
        for line in lines[1:-1]:  # Skip first and last lines (rule header and footer)
            line = line.strip()
            
            # Handle for loops
            if line.startswith("for"):
                parts = line.split()
                var = parts[1]
                container = parts[3]
                
                # Convert scene.Object1 to scene.get("Object1", [])
                container_parts = container.split('.')
                get_chain = f"{container_parts[0]}.get('{container_parts[1]}', [])"
                
                py_code += f"{indent}for {var} in {get_chain}:\n"
                indent = "    " * 2
            
            # Handle if conditions
            elif line.startswith("if"):
                condition = line[2:].split("then")[0].strip()
                
                # Handle count conditions
                if condition.startswith("count("):
                    # Extract parts like count(scene.Object1.shape) >= 5
                    cond_parts = condition.split()
                    count_expr = cond_parts[0][6:-1]  # Remove "count(" and ")"
                    op = cond_parts[1]
                    val = cond_parts[2]
                    
                    # Convert scene.Object1.shape to scene.get("Object1", [])
                    count_parts = count_expr.split('.')
                    if len(count_parts) == 2:  # Just counting objects
                        get_chain = f"{count_parts[0]}.get('{count_parts[1]}', [])"
                        py_code += f"{indent}if len({get_chain}) {op} {val}:\n"
                    else:  # Counting attributes
                        get_chain = f"{count_parts[0]}.get('{count_parts[1]}', [])"
                        attr = count_parts[2]
                        py_code += f"{indent}if sum(1 for obj in {get_chain} if obj.attributes.get('{attr}')) {op} {val}:\n"
                
                indent = "    " * (line.count('    ') + 1)
            
            # Handle contradictions
            elif line.startswith("contradiction"):
                contra_code = line.split()[1]
                py_code += f"{indent}return 'contradiction {contra_code}'\n"
                indent = "    " * (line.count('    ') - 1)
        
        py_code += f"{indent}return None\n\n"
        python_methods[rule_name] = py_code
    
    return python_methods

# Generate Python methods
python_methods = generate_python_methods_from_strings(rule_strings)

print("=== GENERATED PYTHON METHODS ===")
for name, method in python_methods.items():
    print(f"# From rule: {name}")
    print(method)


