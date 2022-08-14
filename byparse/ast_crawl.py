from logging import warning
import os
from pathlib import Path
from typing import Dict, Optional, Union

import ast
import networkx as nx

from byparse.utils import pretty_path_name


class AstContextCrawler:
    root_ast: Union[ast.Module, ast.FunctionDef, ast.ClassDef]

    functions: Dict[ast.FunctionDef, "AstContextCrawler"]
    classes: Dict[ast.ClassDef, "AstContextCrawler"]

    imports: Dict[str, Union[ast.Import, ast.ImportFrom]]
    calls: Dict[str, ast.Call]

    def __init__(
        self, root_ast: Union[ast.Module, ast.FunctionDef, ast.ClassDef]
    ) -> None:
        self.root_ast = root_ast
        self.imports = {}
        self.calls = {}
        self.functions = {}
        self.classes = {}

        if isinstance(root_ast, ast.Module):
            self.crawl(root_ast, self)
        elif isinstance(root_ast, (ast.FunctionDef, ast.ClassDef)):
            for i in root_ast.body:
                self.crawl(i, self)

    def add_import(self, import_ast: Union[ast.Import, ast.ImportFrom]):
        for alias in import_ast.names:
            name = alias.name if alias.asname is None else alias.asname
            if isinstance(import_ast, ast.ImportFrom):
                module, level = (import_ast.module, import_ast.level)
            elif isinstance(import_ast, ast.Import):
                module, level = (None, 0)
            else:
                raise TypeError()
            self.imports[name] = ast.ImportFrom(
                names=[alias], module=module, level=level
            )

    def add_call(self, call_ast: ast.Call):
        self.calls[ast_call_name(call_ast)] = call_ast

    @property
    def known_names(self) -> Dict[str, ast.FunctionDef]:
        names = {}
        names.update(self.functions)
        names.update(self.classes)
        return names

    def crawl(
        self,
        ast_element: Union[ast.AST, Optional[ast.expr]],
        context: "AstContextCrawler",
    ) -> None:
        """Recursive depth-first explorer of the abstract syntax tree.

        Args:
            ast_element (Union[ast.AST, Optional[ast.expr]]): Abstract syntax tree element to crawl.
            context (AstContextCrawler): Context being crawled.

        """
        if ast_element is None:
            return

        context = self if context is None else context

        # Enumerate the types we can encounter
        if isinstance(ast_element, (ast.Import, ast.ImportFrom)):
            context.add_import(ast_element)
        elif isinstance(ast_element, ast.Call):
            context.add_call(ast_element)
            for v in ast_element.args:
                self.crawl(v, context)
        elif isinstance(ast_element, ast.FunctionDef):
            self.functions[ast_element.name] = AstContextCrawler(ast_element)
        elif isinstance(ast_element, ast.ClassDef):
            self.classes[ast_element.name] = AstContextCrawler(ast_element)
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
        ast_elements = ("functions", "classes", "imports", "calls")

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


class ProjectCrawler:
    modules: Dict[Path, ModuleCrawler]

    def __init__(self, project_path: str) -> None:
        self.path = Path(project_path)
        self.modules = self.parse_project()

    def parse_project(self) -> Dict[Path, ModuleCrawler]:
        project_paths = os.walk(self.path)
        modules_asts = {}
        for dirpath, _, filenames in project_paths:
            for filename in filenames:
                if filename.endswith(".py"):
                    filepath = Path(dirpath) / Path(filename)
                    modules_asts[filepath] = ModuleCrawler(filepath, root=self.path)
                elif filename.endswith(".ipynb"):
                    warning(f"Notebooks are not supported yet, ignored {filename}")
        return modules_asts

    def build_contexts_graph(
        self,
        graph: Optional[nx.DiGraph] = None,
        node_folder_color: str = "rgb(155, 155, 55)",
        node_file_color: str = "rgb(55, 155, 55)",
        node_class_color: str = "#4ec994",
        node_func_color: str = "#e0e069",
        edge_path_color: str = "black",
        edge_context_color: str = "blue",
    ) -> nx.DiGraph:

        if graph is None:
            graph = nx.DiGraph()

        def link_path_to_name(path: Path, name: str):
            return ">".join((str(path), name))

        def add_parent_folders(
            path: Path,
            node_color: str = node_folder_color,
            edge_color: str = edge_path_color,
        ):
            parent = path.parent
            if str(parent) != ".":
                graph.add_node(str(parent), label=parent.name, color=node_color)
                graph.add_edge(str(path), str(parent), color=edge_color)
                add_parent_folders(parent)

        def add_sub_contexts(
            context_path: str,
            context: AstContextCrawler,
            node_class_color: str = node_class_color,
            node_func_color: str = node_func_color,
            edge_color: str = edge_context_color,
        ):
            def add_sub_context(attr_name: str, node_color: str, edge_color: str):
                attr_contexts: Dict[str, AstContextCrawler] = getattr(
                    context, attr_name
                )
                for name, subcontext in attr_contexts.items():
                    subcontext_path = link_path_to_name(context_path, name)
                    graph.add_node(
                        subcontext_path,
                        label=name,
                        color=node_color,
                    )
                    graph.add_edge(subcontext_path, context_path, color=edge_color)
                    add_sub_contexts(
                        subcontext_path,
                        subcontext,
                        node_class_color,
                        node_func_color,
                        edge_color,
                    )

            add_sub_context("functions", node_func_color, edge_color)
            add_sub_context("classes", node_class_color, edge_color)

        for module_path, module_crawler in self.modules.items():
            rel_path = module_path.relative_to(self.path)
            graph.add_node(str(rel_path), label=rel_path.name, color=node_file_color)
            add_parent_folders(rel_path)
            add_sub_contexts(str(rel_path), module_crawler.context)

        return graph


def ast_call_name(call: ast.Call):
    call_name = ""
    element = call.func
    while isinstance(element, ast.Attribute):
        call_name = "." + element.attr + call_name
        element = element.value
    if isinstance(element, ast.Name):
        call_name = element.id + call_name
    return call_name
