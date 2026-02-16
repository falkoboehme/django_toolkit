from ..functions.permissions import ALL_OPERATIONS


def get_comment_header(text: str, hash_repeat=3) -> str:
    """Create a comment header for generated code sections"""
    return f"{'#'*hash_repeat} {text} {'#'*hash_repeat}"


def get_view_class_name(model_name: str, operation: str) -> str:
    """Create a view name based on model name and operation"""
    assert (
        operation in ALL_OPERATIONS
    ), f"Invalid operation {operation}. Must be one of {ALL_OPERATIONS}"
    return f"{model_name}{operation.capitalize()}View"


def get_base_view_class(operation: str) -> str:
    """Get the base view class name based on view type"""
    assert (
        operation in ALL_OPERATIONS
    ), f"Invalid operation {operation}. Must be one of {ALL_OPERATIONS}"

    if operation == "list":
        return "DTListView"
    elif operation == "detail":
        return "DTDetailView"
    elif operation == "create":
        return "DTCreateView"
    elif operation == "update":
        return "DTUpdateView"
    elif operation == "delete":
        return "DTDeleteView"
    else:
        raise ValueError(
            f"Invalid operation {operation}. Must be one of {ALL_OPERATIONS}"
        )


def get_table_class_name(model_name: str) -> str:
    """Create a table name based on model name"""
    return f"{model_name}Table"
