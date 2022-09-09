from typing import List
import networkx as nx
from byparse.abc import EdgeType, NodeType


def networkx_to_cytoscape_fcose(graph: nx.MultiDiGraph) -> dict:

    nodes: List[dict] = []
    edges: List[dict] = []

    for source, target, edge_attrs in graph.edges(data=True):
        if edge_attrs["type"] not in (EdgeType.CONTEXT.name, EdgeType.PATH.name):
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


def networkx_to_cytoscape_fcose_constraints(graph: nx.MultiDiGraph) -> dict:

    valign: List[dict] = []
    halign: List[dict] = []
    relative_constraints: List[dict] = []
    nodes_positions: List[dict] = []

    for _, node_attrs in graph.nodes(data=True):
        if node_attrs["type"] == NodeType.CLASS.name and "childs" in node_attrs:
            aligned_childs = [
                node
                for node in node_attrs["childs"]
                if not graph.nodes[node].get("childs", [])
            ]
            halign.append(aligned_childs)
        if node_attrs["type"] == NodeType.FILE.name and "childs" in node_attrs:
            aligned_childs = [
                node
                for node in node_attrs["childs"]
                if not graph.nodes[node].get("childs", [])
            ]
            valign.append(aligned_childs)

    return {
        "alignmentConstraint": {"vertical": valign, "horizontal": halign},
        "relativePlacementConstraint": relative_constraints,
        "fixedNodeConstraint": nodes_positions,
    }
