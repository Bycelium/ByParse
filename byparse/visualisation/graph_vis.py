import networkx as nx

from byparse.abc import NodeType, EdgeType


def compute_parents_and_childs(graph: nx.MultiDiGraph):
    for source, target, edge_attrs in graph.edges(data=True):
        if edge_attrs["type"] in (EdgeType.CONTEXT.name, EdgeType.PATH.name):
            graph.nodes[source]["parent"] = target
            if "childs" in graph.nodes[target]:
                graph.nodes[target]["childs"].append(source)
            else:
                graph.nodes[target]["childs"] = [source]


def color_context_graph(
    graph: nx.MultiDiGraph,
    node_folder_color: str = "#87847c",
    node_file_color: str = "#379b37",
    node_class_color: str = "#4ec994",
    node_func_color: str = "#e0e069",
    node_lib_color: str = "grey",
    edge_path_color: str = "black",
    edge_context_color: str = "blue",
    edge_call_color: str = "#e0e069",
    edge_inheritance_color: str = "#4ec994",
    edge_type_hint_color: str = "#4ec994",
):
    node_type_color = {
        NodeType.FOLDER.name: node_folder_color,
        NodeType.FILE.name: node_file_color,
        NodeType.CLASS.name: node_class_color,
        NodeType.FUNCTION.name: node_func_color,
        NodeType.LIBRAIRY.name: node_lib_color,
    }
    for n, data in graph.nodes(data=True):
        node_type = data["type"]
        if node_type in node_type_color:
            graph.nodes[n]["color"] = node_type_color[node_type]

    edge_type_color = {
        EdgeType.PATH.name: edge_path_color,
        EdgeType.CONTEXT.name: edge_context_color,
        EdgeType.CALL.name: edge_call_color,
        EdgeType.INHERITANCE.name: edge_inheritance_color,
        EdgeType.TYPEHINT.name: edge_type_hint_color,
    }
    edge_type_linestyle = {
        EdgeType.TYPEHINT.name: "dashed",
    }
    for u, v, key, data in graph.edges(data=True, keys=True):
        edge_type = data["type"]
        if edge_type in edge_type_color:
            graph.edges[u, v, key]["color"] = edge_type_color[edge_type]
        if edge_type in edge_type_linestyle:
            graph.edges[u, v, key]["linestyle"] = edge_type_linestyle[edge_type]
        if edge_type == EdgeType.INHERITANCE.name:
            graph.edges[u, v, key]["arrow"] = "diamond"
