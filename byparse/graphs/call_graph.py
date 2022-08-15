from logging import debug, warning
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

import ast
import networkx as nx

from byparse.abc import NodeType, EdgeType
from byparse.utils import link_path_to_name
from byparse.resolve_import import resolve_aliases_paths, resolve_import_ast_paths

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


def add_context_calls_edges(
    graph: nx.DiGraph,
    project: "ProjectCrawler",
    module: "ModuleCrawler",
    context: "AstContextCrawler",
    context_path: Path,
    aliases_paths: Dict["ast.alias", Path] = None,
    used_names: Dict[str, "ast.alias"] = None,
):

    aliases_paths = {} if aliases_paths is None else aliases_paths
    used_names = {} if used_names is None else used_names

    # Add context node
    if isinstance(context_path, Path):
        label = context_path.name
    else:
        label = context_path.split(">")[-1]

    node_type = root_ast_to_node_type(context.root_ast)

    if context_path not in graph.nodes():
        graph.add_node(context_path, label=label, type=node_type)

    # Add local imports
    local_aliases_paths, local_used_names = resolve_aliases_paths(
        context.imports, str(module.root)
    )

    local_aliases_paths.update(aliases_paths)
    local_used_names.update(used_names)

    for call_name, _ in context.calls.items():

        call_path, call_type = resolve_call_path(
            call_name, project, module, local_used_names, local_aliases_paths
        )

        # Finally add the edge
        if not call_path:
            warning(f"Could not find call path for {call_name}")
            continue

        if project.path.root in call_path:
            call_path = Path(call_path).relative_to(project.path)

        if call_path not in graph.nodes():
            graph.add_node(call_path, label=call_name.split(".")[-1], type=call_type)
        graph.add_edge(call_path, context_path, type=EdgeType.CALL.name)

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


def resolve_call_path(
    call_name: str,
    project: "ProjectCrawler",
    module: "ModuleCrawler",
    local_used_names: Dict[str, "ast.alias"],
    local_aliases_paths: Dict["ast.alias", Path],
    with_deps="group",
):
    call_parts = call_name.split(".")

    call_path = None
    if call_name in module.context.known_names:
        # Function or Class in same file
        other_context = module.context.known_names[call_name]
        call_type = root_ast_to_node_type(other_context.root_ast)
        return link_path_to_name(module.path, other_context.root_ast.name), call_type

    level = 0
    call_chain = call_name
    call_end = ""
    while call_chain not in local_used_names and level < len(call_parts):
        # Look for part of module chain in local used names in decreasing lenght of chain
        call_chain = ".".join(call_parts[: 1 - level])
        call_end = ".".join(call_parts[1 - level :])
        level += 1

    if call_chain in local_used_names:
        # Function or Class imported
        alias = local_used_names[call_chain]
        call_true_path: Path = local_aliases_paths[alias]

        # Filter libs
        if "lib" in call_true_path.parts:
            if not with_deps:
                return None, NodeType.LIBRAIRY.name
            if (
                "__init__.py" in call_true_path.parts
                or "__main__.py" in call_true_path.parts
            ):
                call_true_path = call_true_path.parent
            call_true_path = call_true_path.parts[-1]
            call_true_path = call_true_path.split(".py")[0]
            if with_deps == "group":
                call_path = call_true_path
            else:
                call_path = link_path_to_name(call_true_path, call_parts[-1])
            return call_path, NodeType.LIBRAIRY.name

        target = project.modules[call_true_path.relative_to(project.path)]

        while (
            alias.name not in target.context.known_names
            and call_end not in target.context.known_names
        ):
            # Solve chained imports until reaching the functions / class definition
            if alias.name in target.context.imports:
                import_from_ast = target.context.imports[alias.name]
            elif call_end in target.context.imports:
                import_from_ast = target.context.imports[call_end]
            else:
                warning(f"Could not resolve call_chain: {call_name}")
                debug(
                    f"{alias.name} & {call_end} not found in"
                    f" known_names:{list(target.context.known_names.keys())} nor in"
                    f" imports_names:{list(target.context.imports.keys())}"
                )
                return None, None

            target_path = resolve_import_ast_paths(import_from_ast, str(target.root))
            target_path = list(target_path.values())[0]
            target = project.modules[target_path.relative_to(project.path)]
            call_true_path = target_path

        if (
            alias.name in target.context.functions
            or call_end in target.context.functions
        ):
            call_type = NodeType.FUNCTION.name
        elif alias.name in target.context.classes or call_end in target.context.classes:
            call_type = NodeType.CLASS.name

        return link_path_to_name(call_true_path, call_parts[-1]), call_type

    return None, None


def root_ast_to_node_type(root_ast: ast.AST) -> str:
    if isinstance(root_ast, ast.FunctionDef):
        return NodeType.FUNCTION.name
    elif isinstance(root_ast, ast.ClassDef):
        return NodeType.CLASS.name
    elif isinstance(root_ast, ast.Module):
        return NodeType.FILE.name
    else:
        raise TypeError()
