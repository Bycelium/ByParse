import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import ast

from byparse.utils import pretty_path_name


class ModuleAst:
    root: Path
    path: Path
    source: str
    imports: List[Union[ast.Import, ast.ImportFrom]]
    functions: Dict[ast.FunctionDef, List[ast.Call]]
    classes: Dict[ast.ClassDef, List[ast.Call]]
    calls: List[ast.Call]

    def __init__(self, path: Union[str, Path], root: Union[str, Path]):
        self.root = Path(root)
        self.path = Path(path)
        self.name = pretty_path_name(self.path)

        with open(self.path, "r", encoding="utf8") as file:
            self.source = file.read()

        module_ast = ast.parse(source=self.source, filename=self.path.name)
        assert isinstance(module_ast, ast.Module)

        self.imports = []
        self.calls = []
        self.functions = {}
        self.classes = {}
        # Imports and call used
        self.crawler_ast(module_ast)

    def crawler_ast(
        self,
        ast_element: Union[ast.AST, Optional[ast.expr]],
        context: Optional[list] = None,
    ) -> None:
        """Recursive depth-first explorer of the abstract syntax tree.

        Args:
            s (Union[ast.AST, Optional[ast.expr]]): #TODO
            namespace (Optional[str]): #TODO
            import_resolution (bool): #TODO

        """
        if ast_element is None:
            return
        # Enumerate the types we can encounter
        if isinstance(ast_element, (ast.Import, ast.ImportFrom)):
            if context is not None:
                context.append(ast_element)
            else:
                self.imports.append(ast_element)
        elif isinstance(ast_element, ast.Call):
            if context is not None:
                context.append(ast_element)
            else:
                self.calls.append(ast_element)
            for v in ast_element.args:
                self.crawler_ast(v, context)
        elif isinstance(ast_element, ast.FunctionDef):
            self.functions[ast_element] = []
            for i in ast_element.body:
                self.crawler_ast(i, self.functions[ast_element])
        elif isinstance(ast_element, ast.ClassDef):
            self.classes[ast_element] = []
            for i in ast_element.body:
                self.crawler_ast(i, self.classes[ast_element])
        elif isinstance(
            ast_element,
            (
                ast.Module,
                ast.If,
                ast.For,
                ast.While,
                ast.With,
                ast.ExceptHandler,
            ),
        ):
            for i in ast_element.body:
                self.crawler_ast(i, context)

        elif isinstance(ast_element, ast.Try):
            for i in ast_element.body:
                self.crawler_ast(i, context)
            for j in ast_element.handlers:
                self.crawler_ast(j, context)
            for k in ast_element.finalbody:
                self.crawler_ast(k, context)
        elif isinstance(
            ast_element,
            (
                ast.Assign,
                ast.AugAssign,
                ast.AnnAssign,
                ast.FormattedValue,
                ast.Expr,
                ast.Index,
                ast.Return,
            ),
        ):
            self.crawler_ast(ast_element.value, context)
        elif isinstance(ast_element, ast.Subscript):
            self.crawler_ast(ast_element.value, context)
            self.crawler_ast(ast_element.slice, context)
        elif isinstance(ast_element, ast.BinOp):  # 3 + 5
            self.crawler_ast(ast_element.left, context)
            self.crawler_ast(ast_element.right, context)
        elif isinstance(ast_element, (ast.BoolOp, ast.JoinedStr)):
            for v in ast_element.values:
                self.crawler_ast(v, context)
        elif isinstance(ast_element, ast.Compare):  # "s" not in stuff
            self.crawler_ast(ast_element.left, context)
            for v in ast_element.comparators:
                self.crawler_ast(v, context)
        elif isinstance(ast_element, ast.Yield):
            self.crawler_ast(ast_element.value, context)
        elif isinstance(ast_element, ast.Raise):
            self.crawler_ast(ast_element.exc, context)
        elif isinstance(ast_element, (ast.List, ast.Tuple)):
            for v in ast_element.elts:
                self.crawler_ast(v, context)
        elif isinstance(ast_element, ast.Dict):
            for v in ast_element.keys:
                self.crawler_ast(v, context)
            for v in ast_element.values:
                self.crawler_ast(v, context)
        elif isinstance(ast_element, ast.Attribute):
            pass  # variable inside class (np.array)
        elif isinstance(ast_element, ast.Name):
            pass  # variable outside class
        else:
            # Ignore these, they do not contain nested statements
            pass

    def __repr__(self) -> str:
        ast_elements = ("functions", "classes", "imports", "imperative")

        elements_to_print = []
        for key in ast_elements:
            values = getattr(self, key)
            if values:
                print_values = str(len(values))
                if key == "functions":
                    print_values = str([val.name for val in values])
                if key == "imports":
                    print_values = []
                    for val in values:
                        if isinstance(val, ast.Import):
                            print_values += [alias.name for alias in val.names]
                        if isinstance(val, ast.ImportFrom):
                            print_values += [
                                ".".join((val.module, alias.name))
                                for alias in val.names
                            ]
                    print_values = str(print_values)
                elements_to_print.append(f"{key.capitalize()}({print_values})")

        content = ", ".join(elements_to_print)
        return f"ModuleAST({self.path}, {content})"


def parse_project(project_path: str) -> List[ModuleAst]:
    project_paths = os.walk(project_path)
    modules_asts = []
    for dirpath, _, filenames in project_paths:
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = Path(dirpath) / Path(filename)
                modules_asts.append(ModuleAst(filepath, root=project_path))
    return modules_asts


def ast_call_name(call: ast.Call):
    call_name = ""
    element = call.func
    while isinstance(element, ast.Attribute):
        call_name = "." + element.attr + call_name
        element = element.value
    if isinstance(element, ast.Name):
        call_name = element.id + call_name
    return call_name


def ast_call_names(calls: List[ast.Call]):
    return [ast_call_name(call) for call in calls]
