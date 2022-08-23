from typing import List
import networkx as nx
from byparse.abc import EdgeType


def networkx_to_cytoscape_fcose(graph: nx.Graph) -> dict:

    nodes: List[dict] = []
    edges: List[dict] = []

    for source, target, edge_attrs in graph.edges(data=True):
        if edge_attrs["type"] in (EdgeType.CONTEXT.name, EdgeType.PATH.name):
            graph.nodes[source]["parent"] = target
        else:
            edges.append(
                {
                    "data": {
                        "id": f"{source}->{target}",
                        "source": source,
                        "target": target,
                        "arrow": edge_attrs.get("arrow", "triangle-backcurve"),
                        **edge_attrs,
                    }
                }
            )

    for node, node_attrs in graph.nodes(data=True):
        nodes.append({"data": {"id": node, **node_attrs}})

    return {"nodes": nodes, "edges": edges}
