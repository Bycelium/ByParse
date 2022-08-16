from typing import Dict, Optional, Tuple, Union

import ast
from pathlib import Path
from importlib.util import find_spec
from byparse.logging_utils import get_logger

LOGGER = get_logger(__name__)


def resolve_aliases_paths(
    imports: Dict[str, Union[ast.Import, ast.ImportFrom]],
    project_root: str,
) -> Tuple[Dict[ast.alias, Path], Dict[str, ast.alias]]:
    aliases_to_paths: Dict[ast.alias, Path] = {}
    for import_element in imports.values():
        aliases_to_paths.update(
            resolve_import_ast_paths(import_element, project_root=project_root)
        )

    name_to_alias: Dict[str, ast.alias] = {}
    for alias in aliases_to_paths:
        used_name = alias.asname if alias.asname is not None else alias.name
        name_to_alias[used_name] = alias

    return aliases_to_paths, name_to_alias


def resolve_import_ast_paths(
    import_ast: Union[ast.Import, ast.ImportFrom],
    project_root: str,
) -> Dict[ast.alias, Path]:
    alias_paths = {}
    for alias in import_ast.names:
        module = None
        if isinstance(import_ast, ast.ImportFrom):
            module = import_ast.module
        path = resolve_import_ast_alias_path(alias, project_root, module)
        alias_paths[alias] = path
    return alias_paths


def resolve_import_ast_alias_path(
    alias: ast.alias,
    project_root: str,
    module: Optional[str] = None,  # Not none only if ast.ImportFrom
) -> Path:

    if module is not None:  # ImportFrom
        full_chain = ".".join((module, alias.name))

        # For modules and subpackage
        path = _relative_resolution(full_chain, project_root)
        if path is not None:
            return path

        # For functions, classes or global variables imported from module or subpackage
        path = _relative_resolution(module, project_root)
        if path is not None:
            return path

    else:  # Import
        # For modules and subpackage
        path = _relative_resolution(alias.name, project_root)
        if path is not None:
            return path

    # For installed packages
    try:
        spec = find_spec(alias.name)
    except ModuleNotFoundError:
        spec = None

    if spec is None:
        warning_msg = f"{alias.name}"
        if module is not None:
            warning_msg += f" at {module}"
        LOGGER.warning("Could not find a reference for alias %s", warning_msg)
        return Path(f"Lib/site-packages/not-found/{alias.name}")
    if spec.origin == "built-in" or spec.origin is None:
        return Path(f"Lib/site-packages/built-in/{alias.name}")
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
