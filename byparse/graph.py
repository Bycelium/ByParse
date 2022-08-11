import ast
from pathlib import Path
from typing import Dict, List

import networkx as nx

from byparse.ast_crawl import AstContextCrawler, ModuleCrawler, ast_call_name
from byparse.resolve_import import (
    resolve_aliases_paths,
    resolve_import_ast_alias_path,
)


def build_project_graph(module_asts: List[ModuleCrawler]) -> nx.DiGraph:
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
            call_parts = ast_call_name(call).split(".")
            call_import = call_parts[0]
            call_source = call_parts[-1]

            if call_import in module_ast.context.functions_names:
                # Function in same file
                other_func = module_ast.context.functions_names[call_import]
                other_func_path = link_path_to_name(module_ast.path, other_func.name)
                graph.add_edge(other_func_path, edge_endpoint)

            elif call_import in local_used_names:
                # In modules imports
                alias = local_used_names[call_import]
                call_true_path = local_aliases_paths[alias]["path"]
                import_module = local_aliases_paths[alias]["module"]

                if len(call_parts) > 2:
                    # In call used chained attributes
                    # we need to look for the true import path of the submodule
                    import_alias = ast.alias(name=call_source)

                    module_parts = []
                    if import_module is not None:
                        module_parts += [import_module]
                    module_parts += call_parts[:-1]
                    module = ".".join(module_parts)
                    call_true_path = resolve_import_ast_alias_path(
                        import_alias, module_ast.root, module=module
                    )

                call_path = link_path_to_name(call_true_path, call_source)
                if "sbs2" in str(call_source):
                    print(
                        module_ast.path,
                        call_parts,
                        call_path,
                        call_path in graph.nodes(),
                    )
                graph.add_edge(call_path, edge_endpoint)

    # Add nodes
    for module_ast in module_asts:
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
    for module_ast in module_asts:

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
