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
                        print(
                            alias.name,
                            fnames + cnames,
                            alias.name in fnames + cnames,
                        )
                else:
                    graph.add_node(path, label=pretty_path_name(path), ast=None)
                graph.add_edge(path, module_ast.path)
    return graph
