import networkx as nx
import matplotlib.pyplot as plt

from byparse import PythonSourceFile


def to_directed_graph(psf: PythonSourceFile) -> nx.DiGraph:
    G = nx.DiGraph()
    # Simple BFS algorithm with a set to avoid infinite loops.
    visit_stack = [psf]
    visited = set()

    while len(visit_stack) > 0:
        node = visit_stack.pop()
        if node in visited:
            continue
        visited.add(node)
        G.add_node(node.unique_name)
        for i in node.import_paths:
            inst: PythonSourceFile = PythonSourceFile.instances[i]
            visit_stack.append(inst)
            if not G.has_node(inst.unique_name):
                G.add_node(inst.unique_name)
            G.add_edge(inst.unique_name, node.unique_name)

    return G


def draw_import_graph(psf: PythonSourceFile):
    """Display the import graph with networkx and matplotlib backend."""
    G = to_directed_graph(psf)
    labeldict = {}
    for inst_id in PythonSourceFile.instances:
        labeldict[inst_id] = PythonSourceFile.instances[inst_id].basename

    nx.draw(G, labels=labeldict, with_labels=True)
    plt.show()
