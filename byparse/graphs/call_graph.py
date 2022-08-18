from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

import ast
import networkx as nx

from byparse.abc import NodeType, EdgeType
from byparse.utils import link_path_to_name, root_ast_to_node_type
from byparse.path_resolvers.imports import resolve_aliases_paths
from byparse.path_resolvers.names import resolve_name
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


def asts_to_names(asts: List[ast.AST]):
    annotations_names = []
    for ast_elem in asts:
        if ast_elem is None:
            continue
        elif isinstance(ast_elem, ast.Name):
            annotations_names.append(ast_elem.id)
        elif isinstance(ast_elem, ast.Constant):
            annotations_names.append(ast_elem.value)
        else:
            raise TypeError(f"Unsupported annotation type: {type(ast_elem)}")
    return annotations_names


def add_context_calls_edges(
    graph: nx.DiGraph,
    project: "ProjectCrawler",
    module: "ModuleCrawler",
    context: "AstContextCrawler",
    context_path: Union[Path, str],
    aliases_paths: Dict["ast.alias", Path] = None,
    used_names: Dict[str, "ast.alias"] = None,
):

    # Add local imports
    aliases_paths = {} if aliases_paths is None else aliases_paths
    used_names = {} if used_names is None else used_names

    local_aliases_paths, local_used_names = resolve_aliases_paths(
        context.imports, str(module.root)
    )

    local_aliases_paths.update(aliases_paths)
    local_used_names.update(used_names)

    def add_namelink_edge(name: str, edge_type: EdgeType):
        name_path, name_type = resolve_name(
            name,
            module.context,
            module.path,
            project.path,
            project.modules,
            local_used_names,
            local_aliases_paths,
        )

        if not name_path:
            LOGGER.warning("Could not find path for name: %s", name)
            return

        if project.path.parts[0] in str(name_path):
            name_path = str(Path(name_path).relative_to(project.path))

        if str(name_path) not in graph.nodes():
            graph.add_node(str(name_path), label=name.split(".")[-1], type=name_type)
        graph.add_edge(str(name_path), str(context_path), type=edge_type.name)

    def add_calls_edges():
        for call_name, _ in context.calls.items():

            # Ignore builtins calls
            if call_name in __builtins__:
                continue

            add_namelink_edge(call_name, EdgeType.CALL)

    def add_inheritance_edges():
        for base_name in asts_to_names(context.root_ast.bases):
            add_namelink_edge(base_name, EdgeType.INHERITANCE)

    def add_typehints_edges():
        for name in asts_to_names([x.annotation for x in context.root_ast.args.args]):
            add_namelink_edge(name, EdgeType.TYPEHINT)

    # Add context node
    add_context_node(graph, context_path, context)

    if isinstance(context.root_ast, ast.ClassDef):
        add_inheritance_edges()

    if isinstance(context.root_ast, ast.FunctionDef):
        add_typehints_edges()

    add_calls_edges()

    # Recurse on subcontexts (functions then classes)
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
