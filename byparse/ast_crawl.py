from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Union, Optional

import ast
from byparse.utils import try_open_python_file

if TYPE_CHECKING:
    from byparse.py_src_file import PythonSourceFile


def explore_tree(
    psf: "PythonSourceFile",
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
            explore_tree(psf, i, namespace)
    elif isinstance(s, ast.ClassDef):
        # Ignore args, returns, type_comment and decorator_list
        if namespace is not None:
            psf.function_names.add(namespace + s.name)
        for i in s.body:
            explore_tree(psf, i, None)
    elif isinstance(s, ast.FunctionDef):
        if namespace is not None:
            namespace += s.name + "."
        for i in s.body:
            explore_tree(psf, i, namespace)
    elif isinstance(s, ast.Try):
        for i in s.body:
            explore_tree(psf, i, None)
        for j in s.handlers:
            explore_tree(psf, j, None)
        for k in s.finalbody:
            explore_tree(psf, k, None)
    elif isinstance(s, ast.Import) and import_resolution:
        for name in s.names:
            psf.resolve_import(name.name)
    elif isinstance(s, ast.ImportFrom) and import_resolution:
        for name in s.names:
            module_name = name.name
            if s.module is not None:
                module_name = ".".join((s.module, module_name))
            psf.resolve_import(module_name)

    elif isinstance(s, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
        explore_tree(psf, s.value, None)
    elif isinstance(s, ast.Return):
        explore_tree(psf, s.value, None)
    elif isinstance(s, ast.Index):  # stuff inside [] when indexing array
        explore_tree(psf, s.value, None)
    elif isinstance(s, ast.FormattedValue):  # stuff inside f-strings
        explore_tree(psf, s.value, None)
    elif isinstance(s, ast.Expr):
        explore_tree(psf, s.value, None)
    elif isinstance(s, ast.Subscript):
        explore_tree(psf, s.value, None)
        explore_tree(psf, s.slice, None)
    elif isinstance(s, ast.BinOp):  # 3 + 5
        explore_tree(psf, s.left, None)
        explore_tree(psf, s.right, None)
    elif isinstance(s, ast.BoolOp):
        for vals in s.values:
            explore_tree(psf, vals, None)
    elif isinstance(s, ast.JoinedStr):
        for v in s.values:
            explore_tree(psf, v, None)
    elif isinstance(s, ast.Compare):  # "s" not in stuff
        explore_tree(psf, s.left, None)
        for v2 in s.comparators:
            explore_tree(psf, v2, None)
    elif isinstance(s, ast.Yield):
        explore_tree(psf, s.value, None)
    elif isinstance(s, ast.Raise):
        explore_tree(psf, s.exc, None)
    elif isinstance(s, (ast.List, ast.Tuple)):
        for v3 in s.elts:
            explore_tree(psf, v3, None)
    elif isinstance(s, ast.Dict):
        for v4 in s.keys:
            explore_tree(psf, v4, None)
        for v5 in s.values:
            explore_tree(psf, v5, None)
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
            explore_tree(psf, v6, None)
    else:
        # Ignore these, they do not contain nested statements
        pass


def parse_ast_module(filepath: Path) -> Dict[str, List[ast.AST]]:
    file_content = try_open_python_file(filepath)
    fileelement = ast.parse(source=file_content, filename=filepath.name)

    def filter_instances(*types):
        return list(
            filter(
                lambda x: isinstance(x, types),
                fileelement.body,
            )
        )

    return {
        "imports": filter_instances(ast.Import, ast.ImportFrom),
        "functions": filter_instances(ast.FunctionDef, ast.AsyncFunctionDef),
        "classes": filter_instances(ast.ClassDef),
    }


if __name__ == "__main__":
    path = Path("tests/integration/toy_project/package/__main__.py")
    for key, value in parse_ast_module(path).items():
        print(key, value)
