from pathlib import Path
from typing import Dict, Optional, Union
from enum import Enum, auto

import os
import ast

from logging import warning

import networkx as nx

from byparse.context_crawl import AstContextCrawler
from byparse.utils import pretty_path_name


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


class EdgeType(Enum):
    PATH = auto()
    CONTEXT = auto()


class NodeType(Enum):
    FOLDER = auto()
    FILE = auto()
    CLASS = auto()
    FUNCTION = auto()


def color_context_graph(
    graph: nx.DiGraph,
    node_folder_color: str = "rgb(155, 155, 55)",
    node_file_color: str = "rgb(55, 155, 55)",
    node_class_color: str = "#4ec994",
    node_func_color: str = "#e0e069",
    edge_path_color: str = "black",
    edge_context_color: str = "blue",
):
    node_type_color = {
        NodeType.FOLDER.name: node_folder_color,
        NodeType.FILE.name: node_file_color,
        NodeType.CLASS.name: node_class_color,
        NodeType.FUNCTION.name: node_func_color,
    }
    for n, data in graph.nodes(data=True):
        graph.nodes[n]["color"] = node_type_color[data["type"]]

    edge_type_color = {
        EdgeType.PATH.name: edge_path_color,
        EdgeType.CONTEXT.name: edge_context_color,
    }
    for u, v, data in graph.edges(data=True):
        graph.edges[u, v]["color"] = edge_type_color[data["type"]]


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
    ) -> nx.DiGraph:

        if graph is None:
            graph = nx.DiGraph()

        def link_path_to_name(path: Path, name: str):
            return ">".join((str(path), name))

        def add_parent_folders(path: Path):
            parent = path.parent
            if str(parent) != ".":
                graph.add_node(
                    str(parent), label=parent.name, type=NodeType.FOLDER.name
                )
                graph.add_edge(str(path), str(parent), type=EdgeType.PATH.name)
                add_parent_folders(parent)

        def add_sub_contexts(context_path: str, context: AstContextCrawler):
            def add_sub_context(attr_name: str, node_type: NodeType):
                attr_contexts: Dict[str, AstContextCrawler] = getattr(
                    context, attr_name
                )
                for name, subcontext in attr_contexts.items():
                    subcontext_path = link_path_to_name(context_path, name)
                    graph.add_node(subcontext_path, label=name, type=node_type)
                    graph.add_edge(
                        subcontext_path, context_path, type=EdgeType.CONTEXT.name
                    )
                    add_sub_contexts(subcontext_path, subcontext)

            add_sub_context("functions", NodeType.FUNCTION.name)
            add_sub_context("classes", NodeType.CLASS.name)

        for module_path, module_crawler in self.modules.items():
            rel_path = module_path.relative_to(self.path)
            graph.add_node(str(rel_path), label=rel_path.name, type=NodeType.FILE.name)
            add_parent_folders(rel_path)
            add_sub_contexts(str(rel_path), module_crawler.context)

        return graph
