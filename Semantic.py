from lark import Transformer
from collections import defaultdict

class SemanticChecker(Transformer):
    def __init__(self):
        self.objects = {}
        self.rules = []
        self.errors = []
        self.warnings = []
        self.current_rule = None
        self.current_scope = None
        self.used_types = set()
        self.defined_types = set()

    def object_def(self, items):
        name = items[0].value
        attributes = {}
        
        # Handle attributes which could be a list or already transformed dict
        if isinstance(items[1], list):
            for attr in items[1]:
                if isinstance(attr, tuple) and len(attr) == 2:
                    attributes[attr[0]] = attr[1]
        elif isinstance(items[1], dict):
            attributes = items[1]
        
        if name in self.objects:
            self.errors.append(f"❌ Duplicate object definition: {name}")
        
        self.objects[name] = attributes
        return name

    def attribute(self, items):
        key = items[0].value
        value = items[1]
        
        # Extract actual value from Token or Tree
        if hasattr(value, 'value'):
            value = value.value
        elif hasattr(value, 'children') and value.children:
            value = value.children[0].value if hasattr(value.children[0], 'value') else str(value.children[0])
        
        if key == 'type':
            # Clean the type value by removing quotes if present
            if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            self.defined_types.add(value)
        return (key, value)

    def scene_block(self, items):
        return {'Scene': items[0]}

    def scene_list(self, items):
        return items

    def scene_item(self, items):
        try:
            name = items[0].value
            modifier = None
            
            if len(items) > 1:
                modifier_tree = items[1]
                if hasattr(modifier_tree, 'children') and modifier_tree.children:
                    modifier = modifier_tree.children[0].value
                elif hasattr(modifier_tree, 'value'):
                    modifier = modifier_tree.value
            
            return (name, modifier)
        except Exception as e:
            self.errors.append(f"❌ Error processing scene item: {e}")
            return (None, None)

    def rule_block(self, items):
        try:
            rule_name = items[0].value
            self.current_rule = rule_name
            
            if len(items) > 1 and hasattr(items[1], 'children'):
                rule_body = items[1]
                self.rules.append({
                    'name': rule_name,
                    'body': rule_body
                })
                self.check_rule_body(rule_body)
            
            self.current_rule = None
            return rule_name
        except Exception as e:
            self.errors.append(f"❌ Error processing rule block: {e}")
            return None

    def check_rule_body(self, rule_body):
        if not hasattr(rule_body, 'children'):
            return
            
        for statement in rule_body.children:
            if hasattr(statement, 'data'):
                if statement.data == 'forall_stmt':
                    self.check_forall(statement)
                elif statement.data == 'if_stmt':
                    self.check_if(statement)

    def check_forall(self, forall_stmt):
        try:
            var_name = forall_stmt.children[0].value
            path = self.resolve_path(forall_stmt.children[1])
            body = forall_stmt.children[2] if len(forall_stmt.children) > 2 else None
            
            if not self.verify_path_exists(path):
                self.errors.append(f"❌ [Rule {self.current_rule}] Invalid path: {'.'.join(path)}")
            
            old_scope = self.current_scope
            self.current_scope = (var_name, path)
            if body is not None:
                self.check_rule_body(body)
            self.current_scope = old_scope
        except Exception as e:
            self.errors.append(f"❌ Error in forall statement: {e}")

    def check_if(self, if_stmt):
        try:
            condition = if_stmt.children[0] if len(if_stmt.children) > 0 else None
            body = if_stmt.children[1] if len(if_stmt.children) > 1 else None
            
            if condition is not None:
                self.check_condition(condition)
            if body is not None:
                self.check_rule_body(body)
        except Exception as e:
            self.errors.append(f"❌ Error in if statement: {e}")

    def check_condition(self, condition):
        try:
            for term in condition.find_data('logic_term'):
                if len(term.children) > 0:
                    first_child = term.children[0]
                    if hasattr(first_child, 'data'):
                        if first_child.data == 'path':
                            if len(first_child.children) > 0:
                                path = self.resolve_path(first_child.children[0])
                                if not self.verify_path_exists(path):
                                    self.errors.append(f"❌ [Rule {self.current_rule}] Invalid path in condition: {'.'.join(path)}")
                                obj_type = self.get_type_from_path(path)
                                if obj_type != 'UNKNOWN':
                                    self.used_types.add(obj_type)
                        elif first_child.data == 'count_expr':
                            if len(first_child.children) > 0 and hasattr(first_child.children[0], 'children'):
                                if len(first_child.children[0].children) > 0:
                                    path = self.resolve_path(first_child.children[0].children[0])
                                    if not self.verify_path_exists(path):
                                        self.errors.append(f"❌ [Rule {self.current_rule}] Invalid path in count: {'.'.join(path)}")
        except Exception as e:
            self.errors.append(f"❌ Error checking condition: {e}")

    def validate_scene_composition(self):
        """Check all scene items exist and modifiers are valid"""
        try:
            valid_modifiers = {'*', '+', '?'} | {f'{{{n}..{m}}}' for n in range(10) for m in range(n,10)}
            
            for obj_name, obj_def in self.objects.items():
                if isinstance(obj_def, dict) and 'FullScene' in obj_def:
                    scene_def = obj_def['FullScene']
                    if isinstance(scene_def, dict) and 'Scene' in scene_def:
                        scene_items = scene_def['Scene']
                        if isinstance(scene_items, list):
                            for item in scene_items:
                                if isinstance(item, tuple) and len(item) >= 1:
                                    item_name = item[0]
                                    modifier = item[1] if len(item) > 1 else None
                                    if item_name not in self.objects:
                                        self.errors.append(f"❌ Undefined object in {obj_name}.FullScene: {item_name}")
                                    if modifier and modifier not in valid_modifiers:
                                        self.errors.append(f"❌ Invalid modifier in {obj_name}: {modifier}")
        except Exception as e:
            self.errors.append(f"❌ Error validating scene composition: {e}")

    def check_circular_dependencies(self):
        """Detect circular references in scene compositions"""
        try:
            graph = defaultdict(set)
            for name, obj_def in self.objects.items():
                if isinstance(obj_def, dict) and 'FullScene' in obj_def:
                    scene_def = obj_def['FullScene']
                    if isinstance(scene_def, dict) and 'Scene' in scene_def:
                        scene_items = scene_def['Scene']
                        if isinstance(scene_items, list):
                            for item in scene_items:
                                if isinstance(item, tuple) and len(item) >= 1:
                                    graph[name].add(item[0])
            
            visited = set()
            path = set()
            
            def has_cycle(node):
                if node in path:
                    return True
                if node in visited:
                    return False
                    
                visited.add(node)
                path.add(node)
                
                for neighbor in graph.get(node, []):
                    if has_cycle(neighbor):
                        return True
                        
                path.remove(node)
                return False
                
            for node in graph:
                if has_cycle(node):
                    self.errors.append(f"❌ Circular dependency detected involving: {node}")
                    break
        except Exception as e:
            self.errors.append(f"❌ Error checking circular dependencies: {e}")

    def check_required_attributes(self):
        """Verify required attributes per object type"""
        try:
            # First collect all attributes used by each type
            type_attributes = defaultdict(set)
            for obj_name, obj_def in self.objects.items():
                if isinstance(obj_def, dict) and 'type' in obj_def:
                    type_val = obj_def['type']
                    # Normalize type value
                    if isinstance(type_val, str):
                        if type_val.startswith('"') and type_val.endswith('"'):
                            type_val = type_val[1:-1]
                    
                    # Collect all attributes for this type
                    for attr in obj_def.keys():
                        if attr != 'type':
                            type_attributes[type_val].add(attr)
            
            # Now check that all objects of each type have the same attributes
            for type_name, attrs in type_attributes.items():
                for obj_name, obj_def in self.objects.items():
                    if isinstance(obj_def, dict) and 'type' in obj_def:
                        obj_type = obj_def['type']
                        # Normalize type value
                        if isinstance(obj_type, str):
                            if obj_type.startswith('"') and obj_type.endswith('"'):
                                obj_type = obj_type[1:-1]
                        
                        if obj_type == type_name:
                            missing_attrs = attrs - set(obj_def.keys())
                            if missing_attrs:
                                self.errors.append(
                                    f"❌ Object {obj_name} (type: {type_name}) is missing "
                                    f"required attributes: {', '.join(missing_attrs)}"
                                )
        except Exception as e:
            self.errors.append(f"❌ Error checking required attributes: {e}")

    def check_type_consistency(self):
        """Ensure type values are properly quoted and valid"""
        try:
            for obj_name, obj_def in self.objects.items():
                if isinstance(obj_def, dict) and 'type' in obj_def:
                    type_val = obj_def['type']
                    if not (isinstance(type_val, str) and type_val.startswith('"') and type_val.endswith('"')):
                        self.errors.append(f"❌ Type value must be quoted string in {obj_name}")
        except Exception as e:
            self.errors.append(f"❌ Error checking type consistency: {e}")

    def check_rule_coverage(self):
        """Verify all defined types are used in rules"""
        try:
            unused_types = self.defined_types - self.used_types
            for type_name in unused_types:
                self.warnings.append(f"⚠️ Type '{type_name}' is defined but never used in rules")
        except Exception as e:
            self.errors.append(f"❌ Error checking rule coverage: {e}")

    def resolve_path(self, path_tree):
        """Resolve a path expression to a list of strings"""
        try:
            return [token.value for token in path_tree.children]
        except Exception as e:
            self.errors.append(f"❌ Error resolving path: {e}")
            return []

    def verify_path_exists(self, path):
        """Verify that a path exists in the object hierarchy"""
        try:
            current = self.objects
            for part in path:
                if part not in current:
                    return False
                current = current[part]
            return True
        except Exception as e:
            self.errors.append(f"❌ Error verifying path existence: {e}")
            return False

    def get_type_from_path(self, path):
        """Get the type of object at the end of a path"""
        try:
            current = self.objects
            for part in path[:-1]:
                current = current.get(part, {})
            return current.get(path[-1], {}).get('type', 'UNKNOWN')
        except Exception as e:
            self.errors.append(f"❌ Error getting type from path: {e}")
            return 'UNKNOWN'

    def run_all_checks(self, tree):
        """Run all validation passes on the parsed tree"""
        try:
            self.transform(tree)
            
            # Structural validations
            self.validate_scene_composition()
            self.check_circular_dependencies()
            
            # Attribute validations
            self.check_required_attributes()
            self.check_type_consistency()
            
            # Rule validations
            self.check_rule_coverage()
            
            self.report()
        except Exception as e:
            self.errors.append(f"❌ Critical error during semantic analysis: {e}")
            self.report()
            raise

    def report(self):
        """Print all findings"""
        if self.warnings:
            print("\n⚠️ Warnings:")
            for warning in sorted(set(self.warnings)):
                print(f"  - {warning}")
                
        if self.errors:
            print("\n❌ Errors:")
            for error in sorted(set(self.errors)):
                print(f"  - {error}")
        elif not self.warnings:
            print("\n✅ All checks passed!")
        else:
            print("\n⚠️ Checks passed with warnings")