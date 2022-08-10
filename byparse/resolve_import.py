from typing import Dict, Optional, Union

import ast
from pathlib import Path
from importlib.util import find_spec


def resolve_import_ast_paths(
    import_ast: Union[ast.Import, ast.ImportFrom],
    project_root: str,
) -> Dict[ast.alias, Path]:
    alias_paths = {}
    for alias in import_ast.names:
        module = None
        if isinstance(import_ast, ast.ImportFrom):
            module = import_ast.module
        alias_paths[alias] = {
            "path": resolve_import_ast_alias_path(alias, project_root, module),
            "module": module,
        }
    return alias_paths


def resolve_import_ast_alias_path(
    alias: ast.alias,
    project_root: str,
    module: Optional[str] = None,  # Not none only if ast.ImportFrom
) -> Path:

    if module is not None:
        full_chain = ".".join((module, alias.name))

        # For modules and subpackage
        path = _relative_resolution(full_chain, project_root)
        if path is not None:
            return path

        # For functions, classes or global variables imported from module or subpackage
        path = _relative_resolution(module, project_root)
        if path is not None:
            return path

    else:
        # For modules and subpackage
        path = _relative_resolution(alias.name, project_root)
        if path is not None:
            return path

    # For installed packages
    spec = find_spec(alias.name)
    if spec is None:
        raise ModuleNotFoundError(f"Could not find module {alias.name}")
    if spec.origin == "built-in" or spec.origin is None:
        return Path(f"built-in/{alias.name}")
    return Path(spec.origin)


def _relative_resolution(module_chain: str, project_root: str) -> Optional[Path]:
    def mod_to_path(module_chain: str, asfile=False) -> Path:
        str_path = module_chain.replace(".", "/")
        if asfile:
            str_path += ".py"
        return Path(project_root) / Path(str_path)

    # File
    path = mod_to_path(module_chain, asfile=True)
    if path.exists() and path.is_file():
        return path

    # Folder
    path = mod_to_path(module_chain, asfile=False)
    if path.exists() and path.is_dir():
        return path / Path("__init__.py")
