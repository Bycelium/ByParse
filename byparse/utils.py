import ast
from pathlib import Path
from typing import Union

from byparse.abc import NodeType


def pretty_path_name(path: Path):
    name = path.name
    if name in ("__init__.py", "__main__.py"):
        suffix = path.name[:-3].replace("_", "")
        name = f"{path.parent.name}({suffix})"
    return name


def link_path_to_name(path: Union[Path, str], name: str):
    return ">".join((str(path), name))


def ast_call_name(call: ast.Call):
    call_name = ""
    element = call.func
    while isinstance(element, ast.Attribute):
        call_name = "." + element.attr + call_name
        element = element.value
    if isinstance(element, ast.Name):
        call_name = element.id + call_name
    return call_name


def root_ast_to_node_type(root_ast: ast.AST) -> str:
    if isinstance(root_ast, ast.FunctionDef):
        return NodeType.FUNCTION.name
    elif isinstance(root_ast, ast.ClassDef):
        return NodeType.CLASS.name
    elif isinstance(root_ast, ast.Module):
        return NodeType.FILE.name
    else:
        raise TypeError()
