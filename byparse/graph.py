import ast
from logging import debug, warn, warning
from pathlib import Path
from typing import Dict, List

import networkx as nx

from byparse.context_crawl import AstContextCrawler, ast_call_name
from byparse.project_crawl import ModuleCrawler, ProjectCrawler
from byparse.resolve_import import resolve_aliases_paths, resolve_import_ast_alias_path


def build_project_graph(
    project: ProjectCrawler,
    with_deps="group",
) -> nx.DiGraph:
    graph = nx.DiGraph()

    def link_path_to_name(path: Path, name: str):
        return ">".join((str(path), name))

    def add_module_ast_nodes(names: List[str], path: Path, root: Path, color: str):
        for name in names:
            linked_path = link_path_to_name(path, name)
            rpath = Path(linked_path).relative_to(root)
            graph.add_node(linked_path, label=str(rpath), color=color)

    def add_function_calls_edges(
        module_ast: ModuleCrawler,
        edge_endpoint: str,
        context: AstContextCrawler,
        aliases_paths: Dict[ast.alias, Path],
        used_names: Dict[str, ast.alias],
    ):

        # Add local imports
        local_aliases_paths, local_used_names = resolve_aliases_paths(
            context.imports, str(module_ast.root)
        )
        local_aliases_paths.update(aliases_paths)
        local_used_names.update(used_names)

        for call in context.calls:
            call_name = ast_call_name(call)
            call_parts = call_name.split(".")

            call_path = None
            if call_name in module_ast.context.known_names:
                # Function or Class in same file
                other = module_ast.context.known_names[call_name]
                call_path = link_path_to_name(module_ast.path, other.name)
                graph.add_edge(call_path, edge_endpoint)
                continue

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
                        continue
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
                    if call_path not in graph.nodes():
                        graph.add_node(call_path, color="#afaaaf")
                    graph.add_edge(call_path, edge_endpoint)
                    continue

                target = project.modules[call_true_path]

                while (
                    alias.name not in target.context.known_names
                    and call_end not in target.context.known_names
                ):
                    # Solve chained imports until reaching the functions / class definition
                    if alias.name in target.context.imports_names:
                        import_from_ast = target.context.imports_names[alias.name]
                    elif call_end in target.context.imports_names:
                        import_from_ast = target.context.imports_names[call_end]
                    else:
                        warning(f"Could not resolve call_chain: {call_name}")
                        debug(
                            f"{alias.name} & {call_end} not found in"
                            f" known_names:{list(target.context.known_names.keys())} nor in"
                            f" imports_names:{list(target.context.imports_names.keys())}"
                        )
                        break

                    module = import_from_ast.module
                    target_alias = import_from_ast.names[0]

                    target_path = resolve_import_ast_alias_path(
                        target_alias, str(target.root), module
                    )
                    target = project.modules[target_path]
                    call_true_path = target_path

                call_path = link_path_to_name(call_true_path, call_parts[-1])

            # Finally add the edge
            if not call_path:
                warn(f"Could not find call path for {call_name}")
                continue
            graph.add_edge(call_path, edge_endpoint)

    # Add nodes
    for module_ast in project.modules.values():
        add_module_ast_nodes(
            [f.name for f in module_ast.context.functions.keys()],
            path=module_ast.path,
            root=module_ast.root,
            color="#e0e069",
        )
        add_module_ast_nodes(
            [c.name for c in module_ast.context.classes.keys()],
            path=module_ast.path,
            root=module_ast.root,
            color="#4ec994",
        )

    # Add edges
    for module_ast in project.modules.values():

        aliases_paths, used_names = resolve_aliases_paths(
            module_ast.context.imports, str(module_ast.root)
        )

        # Calls in classes methods
        for clas, class_context in module_ast.context.classes.items():
            class_path = link_path_to_name(module_ast.path, clas.name)
            for func, context in class_context.functions.items():
                add_function_calls_edges(
                    module_ast, class_path, context, aliases_paths, used_names
                )

        # Calls in functions
        for func, context in module_ast.context.functions.items():
            func_path = link_path_to_name(module_ast.path, func.name)
            add_function_calls_edges(
                module_ast, func_path, context, aliases_paths, used_names
            )

    return graph
