import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import ast

from byparse.utils import pretty_path_name


class AstContextCrawler:

    functions: Dict[ast.FunctionDef, "AstContextCrawler"]
    classes: Dict[ast.ClassDef, "AstContextCrawler"]

    imports: List[Union[ast.Import, ast.ImportFrom]]
    calls: List[ast.Call]

    def __init__(
        self, root_ast: Union[ast.Module, ast.FunctionDef, ast.ClassDef]
    ) -> None:
        self.root_ast = root_ast
        self.imports = []
        self.calls = []
        self.functions = {}
        self.classes = {}

        if isinstance(root_ast, ast.Module):
            self.crawl(root_ast, self)
        elif isinstance(root_ast, (ast.FunctionDef, ast.ClassDef)):
            for i in root_ast.body:
                self.crawl(i, self)

    @property
    def functions_names(self) -> Dict[str, ast.FunctionDef]:
        return {func_def.name: func_def for func_def in self.functions}

    @property
    def classes_names(self) -> Dict[str, ast.FunctionDef]:
        return {class_def.name: class_def for class_def in self.classes}

    @property
    def known_names(self) -> Dict[str, ast.FunctionDef]:
        names = {}
        names.update(self.functions_names)
        names.update(self.classes_names)
        return names

    @property
    def imports_aliases(self):
        aliases: Dict[str, Dict[str, Union[ast.alias, str]]] = {}
        for imp in self.imports:
            module = imp.module if hasattr(imp, "module") else None
            for alias in imp.names:
                name = alias.name if alias.asname is None else alias.asname
                aliases[name] = {"alias": alias, "module": module}
        return aliases

    def crawl(
        self,
        ast_element: Union[ast.AST, Optional[ast.expr]],
        context: "AstContextCrawler",
    ) -> None:
        """Recursive depth-first explorer of the abstract syntax tree.

        Args:
            s (Union[ast.AST, Optional[ast.expr]]): #TODO
            namespace (Optional[str]): #TODO
            import_resolution (bool): #TODO

        """
        if ast_element is None:
            return

        context = self if context is None else context

        # Enumerate the types we can encounter
        if isinstance(ast_element, (ast.Import, ast.ImportFrom)):
            context.imports.append(ast_element)
        elif isinstance(ast_element, ast.Call):
            context.calls.append(ast_element)
            for v in ast_element.args:
                self.crawl(v, context)
        elif isinstance(ast_element, ast.FunctionDef):
            self.functions[ast_element] = AstContextCrawler(ast_element)
        elif isinstance(ast_element, ast.ClassDef):
            self.classes[ast_element] = AstContextCrawler(ast_element)
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
                self.crawl(i, context)

        elif isinstance(ast_element, ast.Try):
            for i in ast_element.body:
                self.crawl(i, context)
            for j in ast_element.handlers:
                self.crawl(j, context)
            for k in ast_element.finalbody:
                self.crawl(k, context)
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
            self.crawl(ast_element.value, context)
        elif isinstance(ast_element, ast.Subscript):
            self.crawl(ast_element.value, context)
            self.crawl(ast_element.slice, context)
        elif isinstance(ast_element, ast.BinOp):  # 3 + 5
            self.crawl(ast_element.left, context)
            self.crawl(ast_element.right, context)
        elif isinstance(ast_element, (ast.BoolOp, ast.JoinedStr)):
            for v in ast_element.values:
                self.crawl(v, context)
        elif isinstance(ast_element, ast.Compare):  # "s" not in stuff
            self.crawl(ast_element.left, context)
            for v in ast_element.comparators:
                self.crawl(v, context)
        elif isinstance(ast_element, ast.Yield):
            self.crawl(ast_element.value, context)
        elif isinstance(ast_element, ast.Raise):
            self.crawl(ast_element.exc, context)
        elif isinstance(ast_element, (ast.List, ast.Tuple)):
            for v in ast_element.elts:
                self.crawl(v, context)
        elif isinstance(ast_element, ast.Dict):
            for v in ast_element.keys:
                self.crawl(v, context)
            for v in ast_element.values:
                self.crawl(v, context)
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
        return f"AstContext({content})"


class ModuleCrawler:
    root: Path
    path: Path
    source: str
    context: AstContextCrawler

    def __init__(self, path: Union[str, Path], root: Union[str, Path]):
        self.root = Path(root)
        self.path = Path(path)
        self.name = pretty_path_name(self.path)

        with open(self.path, "r", encoding="utf8") as file:
            self.source = file.read()

        module_ast = ast.parse(source=self.source, filename=self.path.name)

        # Crawl ast
        self.context = AstContextCrawler(module_ast)


def parse_project(project_path: str) -> List[ModuleCrawler]:
    project_paths = os.walk(project_path)
    modules_asts = []
    for dirpath, _, filenames in project_paths:
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = Path(dirpath) / Path(filename)
                modules_asts.append(ModuleCrawler(filepath, root=project_path))
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
