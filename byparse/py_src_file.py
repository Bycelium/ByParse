import ast
from typing import Optional, Union, Set, Dict, List, Any
from pathlib import Path

import importlib.util
import importlib.machinery

from byparse.identifiers import UniqueIdentifier
from byparse.ast_crawl import explore_tree
from byparse.utils import try_open_python_file


def relative_resolution(pseudo_path: str, relative_to: str) -> Optional[str]:
    # Folder
    package_path: Path = Path(relative_to).parent / Path(pseudo_path)
    if package_path.exists() and package_path.is_dir():
        return str(package_path / Path("__init__.py"))

    # File
    package_path: Path = Path(relative_to).parent / Path(pseudo_path + ".py")
    if package_path.exists() and package_path.is_file():
        return str(package_path)

    return None


def find_relative_path(
    package_name: str, filepath: str, user_cwd: str
) -> Optional[str]:
    """Resolve a local import performed inside filepath by looking at the
    filesystem and searching for a directory or file that the user is trying to import.

    1. Try to resolve the path while ignoring the module path
    2. If that fails, try to resolve it based on the module path

    Args:
        package_name (str): String used in the python code when the user imports
        filepath (str): Path to the python source file where the import is performed.

    Returns:
        (str): Relative path of the file that should be imported.

    Example:
        package_name: scripts.script1 (as part of the statement "import scripts.script1 as s1")
        filepath: ./toy_project/package/__main__.py
        Result: ./toy_project/scripts/script1.py

    """
    pseudo_path = package_name.replace(".", "/")
    package_path = relative_resolution(pseudo_path, filepath)
    if package_path is not None:
        return package_path

    # In case we resolve based on the current working directory, 
    # we introduce a fake file to preserve the relative structure of the directories.
    package_path = relative_resolution(pseudo_path, user_cwd + "/__init__.py")
    if package_path is not None:
        return package_path

    # In case of importing function or class
    pseudo_path = "/".join(pseudo_path.split("/")[:-1])
    package_path = relative_resolution(pseudo_path, filepath)
    if package_path is not None:
        return package_path

    package_path = relative_resolution(pseudo_path, user_cwd + "/__init__.py")
    return package_path


def package_name_to_path(
    package_name: str, filepath: str, user_cwd: str
) -> Optional[str]:
    """
    Return the path of the package named <package_name>
    that was imported from the file located at <filepath>
    """
    try:
        spec = importlib.util.find_spec(package_name, filepath)
    except ModuleNotFoundError:
        # This occurs if an import is dependent on code, and is not supposed to be executed on this OS/Machine
        # We cannot know if imports are really executed or not as we're not solving the halting problem.
        # There is no real way to handle this case perfectly
        # Might handle this differently?
        spec = None

    if spec is None:
        return find_relative_path(package_name, filepath, user_cwd)

    if spec.origin == "built-in" or spec.origin is None:
        return f"built-in/{package_name}"

    return spec.origin


class PythonSourceFile:
    """
    Represents a piece of python code.

    Attributes:
        path (Optional[str]): Path to the python source file.
        basename (str): A short and displayable name for the code, like "utils.py".
        unique_name (Union[UniqueIdentifier, str]): A unique name that always exists.
            If the code is in a file, it is the path. Otherwise, it can be a random string.
        package_name (Optional[str]): If the file is part of a package,
            the name of the package is contained here.
        function_names (Set[str]): Set of functions that are defined by the piece of code.
        import_paths (Set[Union[UniqueIdentifier, str]]): The unique_names of imports.
        instances (Dict[Union[UniqueIdentifier, str], Any]): Static field containing all
            PythonSourceFile instances.
        error_messages (List[str]):
        user_cwd (str): The path of the console of a user that is using the project.
    """

    filepath: Optional[str] = None
    basename: str = ""
    user_cwd: str
    unique_name: Union[UniqueIdentifier, str]
    package_name: Optional[str] = None
    function_names: Set[str] = set()
    import_paths: Set[Union[UniqueIdentifier, str]] = set()
    instances: Dict[Union[UniqueIdentifier, str], Any] = {}
    error_messages: List[str] = []

    def __init__(self, filepath: str, user_cwd: str = ".", parsing: bool = True):
        self.filepath = Path(filepath)
        self.user_cwd = user_cwd
        self.import_paths = set()
        self.function_names = set()
        self.error_messages = []

        assert self.filepath is not None

        self.basename = self.filepath.name
        self.unique_name = filepath
        PythonSourceFile.instances[self.unique_name] = self

        # Perform AST based discovery.
        if self.filepath is not None and parsing:
            filecontent = try_open_python_file(self.filepath)
            try:
                explore_tree(
                    self,
                    ast.parse(source=filecontent, filename=self.filepath.name),
                )
            except SyntaxError as err:
                raise SyntaxError(f"Syntax error inside the file: {filepath}") from err

    def resolve_import(self, import_name: str, exhaustive_resolution=False):
        """Resolve an import based on import_name.

        Keep building the dependency tree based on it.
        This function can create new PythonSourceFile and it thus indirectly recursive.

        Args:
            import_name (str): Name of the import to resolve. Examples:
                'numpy', 'math', 'math.random', 'matplotlib.pyplot'
                '.utils' (in case of from . import utils)
            exhaustive_resolution (bool): If False, ignores native dependencies.
                Default to False.
        """
        package_path = package_name_to_path(import_name, self.filepath, self.user_cwd)

        new_psf = None
        parsing = True

        if package_path is None:
            # Could not resolve package path. We still log it.
            # But only if we're sure this was not already imported
            # (there is an import with the same basename)
            for inst_id in PythonSourceFile.instances:
                if PythonSourceFile.instances[inst_id].basename == import_name:
                    new_psf = PythonSourceFile.instances[inst_id]
                    break

            if new_psf is None:
                package_path = import_name
                parsing = False

        elif not exhaustive_resolution:
            if "built-in" in package_path or "lib" in package_path:
                # Don't resolve native dependencies to avoid noise in graph
                # We create the PythonSourceObject, with without parsing
                parsing = False

        if new_psf is None:
            new_psf = PythonSourceFile(package_path, self.user_cwd, parsing=parsing)

        new_psf.basename = import_name
        self.import_paths.add(new_psf.unique_name)

    def resolve_function_call(self, fn_name):
        if fn_name in self.function_names:
            return self
        else:
            for p in self.import_paths:
                resolved = p.resolveFunctionCall(fn_name)
                if resolved is not None:
                    return resolved
        return None
