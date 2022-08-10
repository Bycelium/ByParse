from typing import List, Optional

import networkx as nx
import matplotlib.pyplot as plt

from byparse.ast_crawl import ModuleAst
from byparse.resolve_import import resolve_import_ast_paths
from byparse.utils import pretty_path_name


def build_project_graph(module_asts: List[ModuleAst]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for module_ast in module_asts:
        graph.add_node(module_ast.path, label=module_ast.name, ast=module_ast)
        for function in module_ast.functions:
            func_path = "/".join((str(module_ast.path), function.name))
            graph.add_node(
                func_path, label=function.name, ast=function, color="#dcdcaa"
            )
            graph.add_edge(func_path, module_ast.path)

    for module_ast in module_asts:
        import_elements = module_ast.imports
        for import_element in import_elements:
            aliase_paths = resolve_import_ast_paths(
                import_element, project_root=module_ast.root
            )

            for alias, path in aliase_paths.items():
                if path in graph.nodes():
                    target_ast: Optional[ModuleAst] = graph.nodes[path]["ast"]
                    if target_ast is not None:
                        fnames = [astf.name for astf in target_ast.functions]
                        cnames = [astc.name for astc in target_ast.classes]
                        if alias.name in fnames + cnames:
                            func_path = "/".join((str(path), alias.name))
                            graph.add_edge(func_path, module_ast.path)
                            continue
                else:
                    graph.add_node(path, label=pretty_path_name(path), ast=None)
                graph.add_edge(path, module_ast.path)
    return graph
