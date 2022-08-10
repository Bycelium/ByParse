import networkx as nx
from pyvis.network import Network  # type: ignore


def networkx_to_pyvis(graph: nx.Graph, width="1920px", height="1080px") -> Network:
    pyvis_graph = Network(height, width, directed=True)

    for node, node_attrs in graph.nodes(data=True):
        label = node_attrs.pop("label", str(node))
        node_attrs.pop("ast", None)
        pyvis_graph.add_node(str(node), label=label, **node_attrs)

    for source, target, edge_attrs in graph.edges(data=True):
        if (
            "value" not in edge_attrs
            and "width" not in edge_attrs
            and "weight" in edge_attrs
        ):
            edge_attrs["value"] = edge_attrs["weight"]
        pyvis_graph.add_edge(str(source), str(target), **edge_attrs)

    return pyvis_graph
