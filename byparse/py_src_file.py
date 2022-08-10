import ast
from typing import Optional, Union, Set, Dict, List, Any
from pathlib import Path

import importlib.util
import importlib.machinery

from byparse.identifiers import UniqueIdentifier


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

    # In case we resolve based on the current working directory, we introduce a fake file to preserve the relative structure
    # of the directories.
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
        self.filepath = filepath
        self.user_cwd = user_cwd
        self.import_paths = set()
        self.function_names = set()
        self.error_messages = []

        assert self.filepath is not None

        self.basename = Path(filepath).name
        self.unique_name = filepath
        PythonSourceFile.instances[self.unique_name] = self

        # Perform AST based discovery.
        if self.filepath is not None and parsing:
            if not self.filepath.endswith(".py"):
                self.error_messages.append(
                    f"Unable to parse a non-python source file: {filepath}"
                )
                return
            filecontent = ""
            try:
                filecontent = open(self.filepath, "r", encoding="utf8").read()
            except OSError as err:
                self.error_messages.append(
                    f"Unable to read file at: {filepath}.\nError: {err}"
                )
                return

            try:
                s = ast.parse(source=filecontent, filename=self.filepath)
                self.explore_tree(s)
            except SyntaxError as err:
                self.error_messages.append(f"Syntax error inside the file: {err}")

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
                # raise ValueError(f"Could not resolve import {import_name}")
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

    def explore_tree(
        self,
        s: Union[ast.AST, Optional[ast.expr]],
        namespace: Optional[str] = "",
        import_resolution=True,
    ) -> None:
        """Recursive depth-first explorer of the abstract syntax tree.

        Args:
            s (Union[ast.AST, Optional[ast.expr]]): #TODO
            namespace (Optional[str]): #TODO
            import_resolution (bool): #TODO

        """
        if s is None:
            return
        # Enumerate the types we can encounter
        if isinstance(
            s, (ast.Module, ast.If, ast.For, ast.While, ast.With, ast.ExceptHandler)
        ):
            for i in s.body:
                self.explore_tree(i, namespace)
        elif isinstance(s, ast.ClassDef):
            # Ignore args, returns, type_comment and decorator_list
            if namespace is not None:
                self.function_names.add(namespace + s.name)
            for i in s.body:
                self.explore_tree(i, None)
        elif isinstance(s, ast.FunctionDef):
            if namespace is not None:
                namespace += s.name + "."
            for i in s.body:
                self.explore_tree(i, namespace)
        elif isinstance(s, ast.Try):
            for i in s.body:
                self.explore_tree(i, None)
            for j in s.handlers:
                self.explore_tree(j, None)
            for k in s.finalbody:
                self.explore_tree(k, None)
        elif isinstance(s, ast.Import) and import_resolution:
            for name in s.names:
                self.resolve_import(name.name)
        elif isinstance(s, ast.ImportFrom) and import_resolution:
            for name in s.names:
                module_name = name.name
                if s.module is not None:
                    module_name = ".".join((s.module, module_name))
                self.resolve_import(module_name)

        elif isinstance(s, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            self.explore_tree(s.value, None)
        elif isinstance(s, ast.Return):
            self.explore_tree(s.value, None)
        elif isinstance(s, ast.Index):  # stuff inside [] when indexing array
            self.explore_tree(s.value, None)
        elif isinstance(s, ast.FormattedValue):  # stuff inside f-strings
            self.explore_tree(s.value, None)
        elif isinstance(s, ast.Expr):
            self.explore_tree(s.value, None)
        elif isinstance(s, ast.Subscript):
            self.explore_tree(s.value, None)
            self.explore_tree(s.slice, None)
        elif isinstance(s, ast.BinOp):  # 3 + 5
            self.explore_tree(s.left, None)
            self.explore_tree(s.right, None)
        elif isinstance(s, ast.BoolOp):
            for vals in s.values:
                self.explore_tree(vals, None)
        elif isinstance(s, ast.JoinedStr):
            for v in s.values:
                self.explore_tree(v, None)
        elif isinstance(s, ast.Compare):  # "s" not in stuff
            self.explore_tree(s.left, None)
            for v2 in s.comparators:
                self.explore_tree(v2, None)
        elif isinstance(s, ast.Yield):
            self.explore_tree(s.value, None)
        elif isinstance(s, ast.Raise):
            self.explore_tree(s.exc, None)
        elif isinstance(s, (ast.List, ast.Tuple)):
            for v3 in s.elts:
                self.explore_tree(v3, None)
        elif isinstance(s, ast.Dict):
            for v4 in s.keys:
                self.explore_tree(v4, None)
            for v5 in s.values:
                self.explore_tree(v5, None)
        elif isinstance(s, ast.Constant):
            pass
        elif isinstance(s, ast.Delete):
            pass
        elif isinstance(s, ast.Attribute):
            pass  # variable inside class (np.array)
        elif isinstance(s, ast.Name):
            pass  # variable outside class
        elif isinstance(s, ast.Call):  # A function call!
            for v6 in s.args:
                self.explore_tree(v6, None)
        else:
            # Ignore these, they do not contain nested statements
            pass

    def resolve_function_call(self, fn_name):
        if fn_name in self.function_names:
            return self
        else:
            for p in self.import_paths:
                resolved = p.resolveFunctionCall(fn_name)
                if resolved is not None:
                    return resolved
        return None
