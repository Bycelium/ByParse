from pathlib import Path
from typing import Dict, List, Optional, Union

import os
import ast
import networkx as nx

from byparse.context_crawl import AstContextCrawler
from byparse.utils import pretty_path_name
from byparse.graphs.context_graph import build_contexts_graph
from byparse.graphs.call_graph import build_call_graph
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
        self.context = AstContextCrawler(module_ast, path=self.path)

    def __str__(self) -> str:
        return (
            f"ModuleCrawler({self.path.relative_to(self.root)}, context={self.context})"
        )


class ProjectCrawler:
    modules: Dict[Path, ModuleCrawler]

    def __init__(self, project_path: str, exclude: Optional[List[str]] = None) -> None:
        self.path = Path(project_path)
        self.modules = self.parse_project(exclude)

    def parse_project(
        self, exclude: Optional[List[str]] = None
    ) -> Dict[Path, ModuleCrawler]:
        modules_asts = {}
        for root, dirs, files in os.walk(self.path, topdown=True):
            if exclude is not None:
                dirs[:] = [d for d in dirs if d not in exclude]
            for filename in files:
                if filename.endswith(".py"):
                    filepath = Path(root) / Path(filename)
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
