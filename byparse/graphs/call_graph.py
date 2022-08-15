from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional, Tuple, Union

import ast
import networkx as nx

from byparse.abc import NodeType, EdgeType
from byparse.utils import link_path_to_name, root_ast_to_node_type
from byparse.path_resolvers.imports import resolve_aliases_paths, resolve_import_ast_paths
from byparse.path_resolvers.calls import resolve_call
from byparse.logging_utils import get_logger

LOGGER = get_logger(__name__)

if TYPE_CHECKING:

    from byparse.context_crawl import AstContextCrawler
    from byparse.project_crawl import ProjectCrawler, ModuleCrawler


def build_call_graph(
    project: "ProjectCrawler",
    graph: Optional[nx.DiGraph] = None,
) -> nx.DiGraph:

    if graph is None:
        graph = nx.DiGraph()

    for module_path, module in project.modules.items():
        add_context_calls_edges(graph, project, module, module.context, module_path)

    return graph


def add_context_node(
    graph: nx.DiGraph, context_path: Union[Path, str], context: "AstContextCrawler"
):
    if isinstance(context_path, Path):
        label = context_path.name
    elif isinstance(context_path, str):
        label = ".".join(context_path.split(">")[1:])
    else:
        raise TypeError()

    node_type = root_ast_to_node_type(context.root_ast)

    if str(context_path) not in graph.nodes():
        graph.add_node(str(context_path), label=label, type=node_type)


def add_context_calls_edges(
    graph: nx.DiGraph,
    project: "ProjectCrawler",
    module: "ModuleCrawler",
    context: "AstContextCrawler",
    context_path: Union[Path, str],
    aliases_paths: Dict["ast.alias", Path] = None,
    used_names: Dict[str, "ast.alias"] = None,
):

    aliases_paths = {} if aliases_paths is None else aliases_paths
    used_names = {} if used_names is None else used_names

    # Add context node
    add_context_node(graph, context_path, context)

    # Add local imports
    local_aliases_paths, local_used_names = resolve_aliases_paths(
        context.imports, str(module.root)
    )

    local_aliases_paths.update(aliases_paths)
    local_used_names.update(used_names)

    for call_name, _ in context.calls.items():

        # Ignore builtins calls
        if call_name in __builtins__:
            continue

        call_path, call_type = resolve_call(
            call_name,
            module.context,
            module.path,
            project.path,
            project.modules,
            local_used_names,
            local_aliases_paths,
        )

        if not call_path:
            LOGGER.warning("Could not find call path for %s", call_name)
            continue

        if project.path.parts[0] in call_path:
            call_path = str(Path(call_path).relative_to(project.path))

        if str(call_path) not in graph.nodes():
            graph.add_node(
                str(call_path), label=call_name.split(".")[-1], type=call_type
            )
        graph.add_edge(str(call_path), str(context_path), type=EdgeType.CALL.name)

    for fname, func_context in context.functions.items():
        fpath = link_path_to_name(context_path, fname)
        add_context_calls_edges(
            graph,
            project,
            module,
            func_context,
            fpath,
            local_aliases_paths,
            local_used_names,
        )

    for cname, class_context in context.classes.items():
        cpath = link_path_to_name(context_path, cname)
        add_context_calls_edges(
            graph,
            project,
            module,
            class_context,
            cpath,
            local_aliases_paths,
            local_used_names,
        )
