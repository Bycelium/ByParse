import os
from pathlib import Path
from typing import List, Union

import ast

from byparse.utils import pretty_path_name


class FunctionAst:
    name: str

    module: "ModuleAst"
    calls: List[ast.Call]

    def __init__(self, module: "ModuleAst", func_def: ast.FunctionDef) -> None:
        self.module = module
        self.name = func_def.name
        self.args = func_def.args
        self.decorator_list = func_def.decorator_list
        self.returns = func_def.returns


class ModuleAst:
    root: Path
    path: Path
    source: str
    imports: List[Union[ast.Import, ast.ImportFrom]]
    functions: List[FunctionAst]
    classes: List[ast.ClassDef]

    def __init__(self, path: Union[str, Path], root: Union[str, Path]):
        self.root = Path(root)
        self.path = Path(path)
        self.name = pretty_path_name(self.path)

        with open(self.path, "r", encoding="utf8") as file:
            self.source = file.read()

        self.parse_ast_module()

    def parse_ast_module(self):
        module_ast = ast.parse(source=self.source, filename=self.path.name)

        assert isinstance(module_ast, ast.Module)

        def filter_instances(*types):
            return list(
                filter(
                    lambda x: isinstance(x, types),
                    module_ast.body,
                )
            )

        self.imports = filter_instances(ast.Import, ast.ImportFrom)
        self.functions = [
            FunctionAst(self, func_def)
            for func_def in filter_instances(ast.FunctionDef, ast.AsyncFunctionDef)
        ]
        self.classes = filter_instances(ast.ClassDef)
        self.imperative = [
            x
            for x in module_ast.body
            if x not in self.imports + self.functions + self.classes
        ]

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
