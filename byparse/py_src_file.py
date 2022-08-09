import ast
from typing import Optional, Union, Set, Dict, List, Any
from pathlib import Path
import importlib.util

from byparse.identifiers import UniqueIdentifier, random_string


def package_name_to_path(package_name: str, filepath: str) -> Optional[str]:
    """
    Return the path of the package named <package_name>
    that was imported from the file located at <filepath>
    """
    spec = None
    try:
        spec = importlib.util.find_spec(package_name, filepath)
    except ModuleNotFoundError:
        # This occurs if an import is dependent on code, and is not supposed to be executed on this OS/Machine
        # We cannot know if imports are really executed or not as we're not solving the halting problem.
        # There is no real way to handle this case perfectly
        pass  # Might handle this differently?
    if spec is not None:
        if spec.origin == "built-in":
            return None
        return spec.origin
    else:
        # Try a local resolve based on filepath:
        package_name = package_name.replace(".", "./")
        package_path: Path = Path(filepath).parent / Path(package_name)
        if package_path.exists():
            if package_path.is_dir():
                return str(package_path / Path("__init__.py"))
            else:
                return str(package_path)
        else:
            package_path = Path(str(package_path) + ".py")
            if package_path.exists():
                return str(package_path)
    return None  # Unable to resolve the package


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

    """

    path: Optional[str] = None
    basename: str = ""
    unique_name: Union[UniqueIdentifier, str]
    package_name: Optional[str] = None
    function_names: Set[str] = set()
    import_paths: Set[Union[UniqueIdentifier, str]] = set()
    instances: Dict[Union[UniqueIdentifier, str], Any] = {}
    error_messages: List[str] = []

    def __init__(self, path, parsing=True):
        self.path = path
        self.import_paths = set()
        self.function_names = set()
        self.error_messages = []

        if self.path is not None:
            self.basename = Path(path).name
            self.unique_name = path
        else:
            self.unique_name = random_string()
        PythonSourceFile.instances[self.unique_name] = self

        # Perform AST based discovery.
        if self.path is not None and parsing:
            if not self.path.endswith(".py"):
                self.error_messages.append(
                    f"Unable to parse a non-python source file: {path}"
                )
                return
            filecontent = ""
            try:
                filecontent = open(self.path, "r", encoding="utf8").read()
            except OSError as err:
                self.error_messages.append(
                    f"Unable to read file at: {path}.\nError: {err}"
                )
                return

            try:
                s = ast.parse(source=filecontent, filename=self.path)
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
        # We don't perform import resolution if the code is not inside a file.
        if self.path is None:
            return
        p = package_name_to_path(import_name, self.path)

        if p is None:
            n = import_name.split(".")
            i = len(n)
            # Try to resolve path to packages of decreasing length.
            while p is None and i > 0:
                p = package_name_to_path(".".join(n[0:i]), self.path)
                i -= 1

            n.insert(0, "")
            i = len(n)
            while p is None and i > 1:
                p = package_name_to_path(".".join(n[0:i]), self.path)
                i -= 1
            if p is None:
                # Give up: we cannot resolve this. We still log it.
                # But only if we're sure this was not already imported (there is an import with the same basename)
                new_psf = None
                for inst_id in PythonSourceFile.instances:
                    if PythonSourceFile.instances[inst_id].basename == import_name:
                        new_psf = PythonSourceFile.instances[inst_id]
                        break
                if new_psf is None:
                    new_psf = PythonSourceFile(None, False)
                new_psf.basename = import_name
                self.import_paths.add(new_psf.unique_name)
                return

        if not exhaustive_resolution:
            if "lib" in p and "site-packages" not in p:
                # Don't resolve native dependencies to avoid noise in graph
                # We create the PythonSourceObject, with without parsing
                new_psf = PythonSourceFile(p, False)
                new_psf.basename = import_name
                self.import_paths.add(new_psf.unique_name)
                return

        new_psf = PythonSourceFile(p)
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
                module_name = "." + name.name
                if s.module is not None:
                    module_name = s.module + module_name
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
            # print(ast.dump(s))
            # print("-----")

    def resolve_function_call(self, fn_name):
        if fn_name in self.function_names:
            return self
        else:
            for p in self.import_paths:
                resolved = p.resolveFunctionCall(fn_name)
                if resolved is not None:
                    return resolved
        return None
