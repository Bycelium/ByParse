import networkx as nx

from byparse.abc import NodeType, EdgeType


def color_context_graph(
    graph: nx.DiGraph,
    node_folder_color: str = "rgb(155, 155, 55)",
    node_file_color: str = "rgb(55, 155, 55)",
    node_class_color: str = "#4ec994",
    node_func_color: str = "#e0e069",
    edge_path_color: str = "black",
    edge_context_color: str = "blue",
):
    node_type_color = {
        NodeType.FOLDER.name: node_folder_color,
        NodeType.FILE.name: node_file_color,
        NodeType.CLASS.name: node_class_color,
        NodeType.FUNCTION.name: node_func_color,
    }
    for n, data in graph.nodes(data=True):
        graph.nodes[n]["color"] = node_type_color[data["type"]]

    edge_type_color = {
        EdgeType.PATH.name: edge_path_color,
        EdgeType.CONTEXT.name: edge_context_color,
    }
    for u, v, data in graph.edges(data=True):
        graph.edges[u, v]["color"] = edge_type_color[data["type"]]
