import ast
from pathlib import Path
from typing import Dict, List

import networkx as nx

from byparse.ast_crawl import ModuleAst, ast_call_name
from byparse.resolve_import import (
    resolve_import_ast_alias_path,
    resolve_import_ast_paths,
)


def build_project_graph(module_asts: List[ModuleAst]) -> nx.DiGraph:
    graph = nx.DiGraph()

    # Add function nodes
    for module_ast in module_asts:
        for func, _ in module_ast.functions.items():
            func_path = ">".join((str(module_ast.path), func.name))
            rpath = Path(func_path).relative_to(Path(module_ast.root))
            graph.add_node(func_path, label=str(rpath), ast=func, color="#dcdcaa")

    # Add edges from calls
    for module_ast in module_asts:

        aliases_paths: Dict[ast.alias, Path] = {}
        for import_element in module_ast.imports:
            aliases_paths.update(
                resolve_import_ast_paths(import_element, project_root=module_ast.root)
            )

        used_names: Dict[str, ast.alias] = {}
        for alias in aliases_paths:
            used_name = alias.asname if alias.asname is not None else alias.name
            used_names[used_name] = alias

        for func, callimps in module_ast.functions.items():
            func_path = ">".join((str(module_ast.path), func.name))
            for callimp in callimps:
                call_parts = ast_call_name(callimp).split(".")
                call_import = call_parts[0]
                call_source = call_parts[-1]
                if call_import in used_names:
                    alias = used_names[call_import]

                    call_true_path = aliases_paths[alias]["path"]
                    if len(call_parts) > 2:
                        import_alias = ast.alias(name=call_source)
                        import_module = aliases_paths[alias]["module"]
                        module_parts = [import_module] + call_parts[:-1]
                        module = ".".join(module_parts)
                        call_true_path = resolve_import_ast_alias_path(
                            import_alias, module_ast.root, module=module
                        )
                    call_path = ">".join((str(call_true_path), call_source))
                    graph.add_edge(call_path, func_path)

    return graph
