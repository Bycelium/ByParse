"""

Read a python package and generate a call graph from it.

To test this, we'll try to analyse scikit learn

"""

import ast
import importlib.util
from pathlib import Path
import os
import networkx as nx # type: ignore
from matplotlib import pyplot as plt # type: ignore
from dataclasses import dataclass, field
from typing import Union, Set, List, Dict, Optional, Any
import random
import string

def random_string(l=12):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(l))

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
        pass # Might handle this differently?
    if spec is not None:
        if spec.origin == "built-in": return None
        return spec.origin
    else:
        # Try a local resolve based on filepath:
        package_name = package_name.replace(".","./")
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
    return None # Unable to resolve the package

def test_package_name_to_path():
    """
    Usage example for package_name_to_path.
    Executable using `pytest to_graph.py -s`
    """
    numpy = package_name_to_path("numpy", ".")
    assert numpy.endswith(str(Path("lib/site-packages/numpy/__init__.py")))

    utils = package_name_to_path("utils", "./toy_project/__main__.py")
    assert utils.endswith(str(Path("utils/__init__.py")))

    pyplot = package_name_to_path("matplotlib.pyplot", ".")
    assert pyplot.endswith(str(Path("lib/site-packages/matplotlib/pyplot.py")))

    doesnotexist = package_name_to_path("doesnotexist", "./toy_project/__main__.py")
    assert doesnotexist is None



@dataclass
class FileLocation:
    """
    Represents a specific place inside a file
    """
    path: str
    lint: int

@dataclass
class UniqueIdentifier:
    """
    A wrapper around a string. Used to indicate that 2 strings are in the same
    context. Used more as a type hint than an actual class.
    """
    v: str

@dataclass
class PythonFunctionDefinition:
    """
    Represents a definition of a python function
    """
    name: str
    arguments: List[str]
    path: str # The file where the function was defined
    line: int
    callingSites: Set[FileLocation]

class PythonSourceFile:
    """
    Represents a piece of python code.
    """
    path: Optional[str] = None

    # A short and displayable name for the code, like "utils.py"
    basename: str = ""
    
    # A unique name that always exists. If the code is in a file, it is the path. Otherwise, it can be a random string.
    unique_name: Union[UniqueIdentifier, str]
 
    # If the file is part of a package, the name of the package is contained here
    package_name: Optional[str] = None

    # The set of functions that are defined by the piece of code
    function_names: Set[str] = set()

    # The unique_names
    import_paths: Set[Union[UniqueIdentifier, str]] = set()

    # Static field containing all PythonSourceFile instances
    instances: Dict[str, Any] = {}

    error_messages: List[str] = []

    def resolveImport(self, importName: str, exhaustiveResolution = False):
        """
            Resolve an import based on importName.
            Keep building the dependency tree based on it.
            This function can create new PythonSourceFile and it thus indirectly recursive.
            importName can look like this:
            - numpy
            - .utils (in case of from . import utils)
            - math
            - math.random
            - matplotlib.pyplot
            All these cases are handled here.
        """
        # We don't perform import resolution if the code is not inside a file.
        if self.path is None: return
        p = package_name_to_path(importName, self.path)
        
        if p is None:
            n = importName.split(".")
            i = len(n)
            # Try to resolve path to packages of decreasing length.
            while p is None and i > 0:
                p = package_name_to_path('.'.join(n[0:i]),self.path)
                i -= 1

            n.insert(0,"")
            i = len(n)
            while p is None and i > 1:
                p = package_name_to_path('.'.join(n[0:i]),self.path)
                i -= 1
            if p is None:
                # Give up: we cannot resolve this. We still log it.
                # But only if we're sure this was not already imported (there is an import with the same basename)
                psf = None
                for i in PythonSourceFile.instances:
                    if PythonSourceFile.instances[i].basename == importName:
                        psf = PythonSourceFile.instances[i]
                        break
                if psf is None:
                    psf = PythonSourceFile(None, False)
                psf.basename = importName
                self.import_paths.add(psf.unique_name)
                return

        if not exhaustiveResolution:
            if "lib" in p and "site-packages" not in p:
                # Don't resolve native dependencies to avoid noise in graph
                # We create the PythonSourceObject, with without parsing
                psf = PythonSourceFile(p, False)
                psf.basename = importName
                self.import_paths.add(psf.unique_name)
                return

        psf = PythonSourceFile(p)
        self.import_paths.add(psf.unique_name)

    def exploreTree(self, s: ast.AST, namespace="", importResolution = True):
        """
            Recursive depth-first explorer of the abstract syntax tree.
        """
        if s is None: return
        # Enumerate the types we can encounter
        if isinstance(s, ast.Module):
            for i in s.body:
                self.exploreTree(i, namespace)
        elif isinstance(s, ast.If) or \
             isinstance(s, ast.For) or \
             isinstance(s, ast.While) or \
             isinstance(s, ast.With) or \
             isinstance(s, ast.ExceptHandler):
            for i in s.body:
                self.exploreTree(i, namespace)
        elif isinstance(s, ast.ClassDef):
            # Ignore args, returns, type_comment and decorator_list
            if namespace is not None:
                self.function_names.add(namespace + s.name)
            for i in s.body:
                self.exploreTree(i, None)
        elif isinstance(s, ast.FunctionDef):
            if namespace is not None:
                namespace += s.name+"."
            for i in s.body:
                self.exploreTree(i, namespace)
        elif isinstance(s, ast.Try):
            for i in s.body:
                self.exploreTree(i, None)
            for j in s.handlers:
                self.exploreTree(j, None)
            for k in s.finalbody:
                self.exploreTree(k, None)
        elif isinstance(s, ast.Import) and importResolution:
            for name in s.names:
                self.resolveImport(name.name)
        elif isinstance(s, ast.ImportFrom) and importResolution:
            for name in s.names:
                if s.module is not None:
                    module_name = s.module + "." + name.name
                    self.resolveImport(module_name)
                else:
                    self.resolveImport("." + name.name)

        elif isinstance(s, ast.Assign):
            # read only the right part of the assignement
            self.exploreTree(s.value, None)
        elif isinstance(s, ast.AugAssign):
            self.exploreTree(s.value, None)
        elif isinstance(s, ast.AnnAssign):
            self.exploreTree(s.value, None)
        elif isinstance(s, ast.Return):
            self.exploreTree(s.value, None)
        elif isinstance(s, ast.Index): # stuff inside [] when indexing array
            self.exploreTree(s.value, None)
        elif isinstance(s, ast.FormattedValue): # stuff inside f-strings
            self.exploreTree(s.value, None)
        elif isinstance(s, ast.Expr):
            self.exploreTree(s.value, None)
        elif isinstance(s, ast.Subscript):
            self.exploreTree(s.value, None)
            self.exploreTree(s.slice, None)
        elif isinstance(s, ast.BinOp): # 3 + 5
            self.exploreTree(s.left, None)
            self.exploreTree(s.right, None)
        elif isinstance(s, ast.BoolOp):
            for i in s.values:
                self.exploreTree(i, None)
        elif isinstance(s, ast.JoinedStr):
            for i in s.values:
                self.exploreTree(i, None)
        elif isinstance(s, ast.Compare): # "s" not in stuff
            self.exploreTree(s.left, None)
            for i in s.comparators:
                self.exploreTree(i, None)
        elif isinstance(s, ast.Yield):
            self.exploreTree(s.value, None)
        elif isinstance(s, ast.Raise):
            self.exploreTree(s.exc, None)
        elif isinstance(s, ast.List) or isinstance(s, ast.Tuple):
            for i in s.elts:
                self.exploreTree(i, None)
        elif isinstance(s, ast.Dict):
            for i in s.keys:
                self.exploreTree(i, None)
            for i in s.values:
                self.exploreTree(i, None)
        elif isinstance(s, ast.Constant):
            pass
        elif isinstance(s, ast.Delete):
            pass
        elif isinstance(s, ast.Attribute):
            pass # variable inside class (np.array)
        elif isinstance(s, ast.Name):
            pass # variable outside class
        elif isinstance(s, ast.Call): # A function call!
            for i in s.args:
                self.exploreTree(i, None)
        else:
            # Ignore these, they do not contain nested statements
            pass
            # print(ast.dump(s))
            # print("-----")

    def to_directed_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        # Simple BFS algorithm with a set to avoid infinite loops.
        visit_stack = [self]
        visited = set()

        while len(visit_stack) > 0:
            node = visit_stack.pop()
            if node in visited: continue
            visited.add(node)
            G.add_node(node.unique_name)
            for i in node.import_paths:
                inst = PythonSourceFile.instances[i]
                visit_stack.append(inst)
                if not G.has_node(inst.unique_name):
                    G.add_node(inst.unique_name)
                G.add_edge(node.unique_name, inst.unique_name)

        return G

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
                self.error_messages.append(f"Unable to parse a non-python source file: {path}")
                return
            filecontent = ""
            try:
                filecontent = open(self.path, "r", encoding="utf8").read()
            except OSError as err:
                self.error_messages.append(f"Unable to read file at: {path}.\nError: {err}")
                return

            try:
                s = ast.parse(source=filecontent, filename=self.path)
                self.exploreTree(s)
            except SyntaxError as err:
                self.error_messages.append(f"Syntax error inside the file: {err}")


    def resolveFunctionCall(self, fn_name):
        if fn_name in self.function_names:
            return self
        else:
            for i in self.import_paths:
                resolved = self.import_paths[i].resolveFunctionCall(fn_name)
                if resolved is not None:
                    return resolved
        return None

if __name__ == "__main__":
    path = "toy_project/__main__.py"
    psf = PythonSourceFile(path=path)
    
    G = psf.to_directed_graph()
    pos = nx.spring_layout(G, k=0.3, iterations=100)

    labeldict = {}
    for i in PythonSourceFile.instances:
        labeldict[i] = PythonSourceFile.instances[i].basename

    nx.draw(G, pos, labels=labeldict, with_labels = True)
    plt.show()