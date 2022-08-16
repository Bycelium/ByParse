from pathlib import Path
from typing import Dict, Optional, Union

import os
import ast
import networkx as nx

from byparse.context_crawl import AstContextCrawler
from byparse.utils import pretty_path_name
from byparse.graphs import build_contexts_graph, build_call_graph
from byparse.logging_utils import get_logger

LOGGER = get_logger(__name__)


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

    def __str__(self) -> str:
        return (
            f"ModuleCrawler({self.path.relative_to(self.root)}, context={self.context})"
        )


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
                    modules_asts[filepath.relative_to(self.path)] = ModuleCrawler(
                        filepath, root=self.path
                    )
                elif filename.endswith(".ipynb"):
                    LOGGER.warning(
                        "Notebooks are not supported yet, ignored %s", filename
                    )
        return modules_asts

    def build_contexts_graph(
        self,
        graph: Optional[nx.DiGraph] = None,
    ) -> nx.DiGraph:
        return build_contexts_graph(self, graph)

    def build_call_graph(
        self,
        graph: Optional[nx.DiGraph] = None,
    ) -> nx.DiGraph:
        return build_call_graph(self, graph)
