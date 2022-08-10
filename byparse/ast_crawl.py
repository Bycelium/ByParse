import os
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Union, Optional

import ast

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


def parse_ast_module(source: str, filename: str) -> Dict[str, List[ast.AST]]:
    module_ast = ast.parse(source=source, filename=filename)

    assert isinstance(module_ast, ast.Module)

    def filter_instances(*types):
        return list(
            filter(
                lambda x: isinstance(x, types),
                module_ast.body,
            )
        )

    ast_filtered = {
        "imports": filter_instances(ast.Import, ast.ImportFrom),
        "functions": filter_instances(ast.FunctionDef, ast.AsyncFunctionDef),
        "classes": filter_instances(ast.ClassDef),
    }
    ast_filtered["imperative"] = [
        x
        for x in module_ast.body
        if x
        not in ast_filtered["imports"]
        + ast_filtered["functions"]
        + ast_filtered["classes"]
    ]

    return ast_filtered


def parse_project(project_path: str) -> Dict[Path, Dict[str, List[ast.AST]]]:
    project_paths = os.walk(project_path)
    file_ast_elements = {}
    for dirpath, _, filenames in project_paths:
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = Path(dirpath) / Path(filename)

                with open(filepath, "r", encoding="utf8") as file:
                    file_src = file.read()

                file_ast_elements[filepath] = parse_ast_module(file_src, filepath.name)
    return file_ast_elements


def pretty_print_ast_elements(file_ast_elements: Dict[Path, Dict[str, List[ast.AST]]]):
    for filepath, ast_elements in file_ast_elements.items():
        print(filepath)
        ast_elements_to_print = {k: v for k, v in ast_elements.items() if v}
        for i, (key, values) in enumerate(ast_elements_to_print.items()):
            prefix = "├" if i < len(ast_elements_to_print) - 1 else "└"
            print_values = str(len(values))
            if key == "functions":
                print_values = [val.name for val in values]
            if key == "imports":
                print_values = []
                for val in values:
                    if isinstance(val, ast.Import):
                        print_values += [alias.name for alias in val.names]
                    if isinstance(val, ast.ImportFrom):
                        print_values += [
                            ".".join((val.module, alias.name)) for alias in val.names
                        ]
            print(prefix, key, print_values)


def main():
    file_ast_elements = parse_project("toy_project")
    pretty_print_ast_elements(file_ast_elements)


if __name__ == "__main__":
    main()
