from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional
import networkx as nx

from byparse.abc import NodeType, EdgeType
from byparse.utils import link_path_to_name

if TYPE_CHECKING:
    from byparse.context_crawl import AstContextCrawler
    from byparse.project_crawl import ProjectCrawler


def build_contexts_graph(
    project: "ProjectCrawler",
    graph: Optional[nx.MultiDiGraph] = None,
) -> nx.MultiDiGraph:

    if graph is None:
        graph = nx.MultiDiGraph()

    for module_path, module_crawler in project.modules.items():
        graph.add_node(
            str(module_path), label=module_path.name, type=NodeType.FILE.name
        )
        _add_parent_folders(graph, module_path)
        _add_sub_contexts(graph, module_path, module_crawler.context)

    return graph


def _add_parent_folders(graph: nx.MultiDiGraph, path: Path):
    parent = path.parent
    if str(parent) != ".":
        graph.add_node(str(parent), label=parent.name, type=NodeType.FOLDER.name)
        graph.add_edge(str(path), str(parent), type=EdgeType.PATH.name)
        _add_parent_folders(graph, parent)


def _add_sub_contexts(
    graph: nx.MultiDiGraph,
    context_path: Path,
    context: "AstContextCrawler",
):
    def _add_sub_context(attr_name: str, node_type: NodeType):
        attr_contexts: Dict[str, "AstContextCrawler"] = getattr(context, attr_name)
        for name, subcontext in attr_contexts.items():
            subcontext_path = link_path_to_name(context_path, name)
            graph.add_node(subcontext_path, label=name, type=node_type)
            graph.add_edge(
                subcontext_path,
                str(context_path),
                type=EdgeType.CONTEXT.name,
            )
            _add_sub_contexts(graph, subcontext_path, subcontext)

    _add_sub_context("functions", NodeType.FUNCTION.name)
    _add_sub_context("classes", NodeType.CLASS.name)
