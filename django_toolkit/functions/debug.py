import json
import inspect
from pprint import pprint

def print_attr(obj, exclude_prefix="__"):
    property_list = []
    function_list = []
    for attr_name in dir(obj):
        if exclude_prefix is None or not attr_name.startswith(exclude_prefix):
            try:
                attr = getattr(obj, attr_name)
            except AttributeError:
                attr = getattr(obj.__class__, attr_name)
            attr_type = type(attr)
            if attr_type.__name__ in ['function', 'method']:
                function_list.append(attr_name)
            elif attr_type in [bool, tuple, int, str, list, dict, type(None), type(type)]:
                property_list.append(attr_name)
            else:
                property_list.append(attr_name)
                #print(f"{attr_name}: {attr_type}: {attr}")
    print(f"{obj} ({type(obj)})")
    print(f"Properties: {property_list}\n")
    print(f"Functions: {function_list}\n")

def print_object_tree(var, depth=0, max_depth=3, indent="    ", exclude_under_start=False, exclude_dunder=True):
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BRIGHT_BLUE = "\033[96m"
    BRIGHT_GREEN = "\033[92m"
    RESET = "\033[0m"

    def print_color(text, color, end="\n"):
        print(f"{color}{text}{RESET}", end=end)
    
    if depth > max_depth:
        return
    indent_str = indent * depth
    
    if inspect.isclass(var) and depth==0:
        print_color(f"{var.__name__}", BRIGHT_GREEN)
    elif inspect.isclass(type(var)) and depth==0:
        print_color(f"Instance of {var.__class__.__name__}", BRIGHT_BLUE)
    
    attributes = dir(var)
    for attr in attributes:
        # print(attr)
        if exclude_dunder and attr.startswith("__") and attr.endswith("__"):
            continue  # Skip built-in attributes and methods
        if exclude_under_start and attr.startswith("_"):
            continue  # Skip under attributes and methods
        try:
            value = getattr(var, attr)
        except Exception as e:
            value = str(e)
        
        value_type = type(value).__name__
        if value_type in ['method', 'function']:
            print_color(f"{indent_str}{indent}{attr}", YELLOW)
        elif value_type == 'builtin_function_or_method':
            pass
        elif value_type == 'property':
            pass
        elif isinstance(value, (int, float, str, bool, tuple, list, dict, type(None))):
            print_color(f"{indent_str}{indent}{attr}", BLUE, end="")
            print(f": {value} {type(value)}")
        elif inspect.isclass(value):
            print_color(f"{indent_str}{indent}{attr}", BRIGHT_GREEN, end="")
            print(f": {value.__name__} {type(value)}")
            print_object_tree(value, depth + 1, max_depth, indent, exclude_under_start, exclude_dunder)
        else:
            print(f"{indent_str}{indent}{attr}: {value_type}")
            

def pp(var):
    pprint(var)

def print_tdc(var):
    print (
            f"=========================\n"
            f"type   : {type(var)}\n"
            f"dir    : {dir(var)}\n"
            f"content: {var}"
        )


def print_tc(var):
    print (
            f"=========================\n"
            f"type   : {type(var)}\n"
            f"content: {var}"
        )

def print_ct(var):
    print(f"{var} ({type(var)})")

def pprint_dict(d):
    print(json.dumps(d, indent=4))
    
    
def dict_pretty(dictionary: dict = {}) -> str:
    return json.dumps(dictionary, indent=4, sort_keys=True, ensure_ascii=False)

def print_json(d):
    print(dict_pretty(d))
