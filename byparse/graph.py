import ast
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx
import matplotlib.pyplot as plt

from byparse.ast_crawl import ModuleAst, ast_call_name
from byparse.resolve_import import (
    resolve_import_ast_alias_path,
    resolve_import_ast_paths,
)
from byparse.utils import pretty_path_name


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

        # print(module_ast.path, aliase_paths)

        # for alias, path in aliase_paths.items():
        #     alias_name = alias.asname if alias.asname is not None else alias.name
        #     print(module_ast.path, alias_name, path)
        # if path in graph.nodes():
        #     target_ast: Optional[ModuleAst] = graph.nodes[path]["ast"]
        #     if target_ast is not None:
        #         for callimp in callimps:
        #             call_name = ast_call_name(callimp)
        #             aliasas = call_name.split(".")[0]
        #             graph.add_edge(, func_path)
        #         fnames = [astf.name for astf in target_ast.functions]
        #         cnames = [astc.name for astc in target_ast.classes]
        #         if alias.name in fnames + cnames:
        #             func_path = "/".join((str(path), alias.name))
        #             graph.add_edge(func_path, module_ast.path)
        #             continue
        # else:
        #     graph.add_node(path, label=pretty_path_name(path), ast=None)
        # graph.add_edge(path, module_ast.path)
    return graph
