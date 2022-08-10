from byparse.visualisation import networkx_to_pyvis
from byparse.ast_crawl import parse_project
from byparse.graph import build_project_graph

if __name__ == "__main__":
    project_root = "tests/integration/toy_project"
    module_asts = parse_project(project_root)
    graph = build_project_graph(module_asts)
    net = networkx_to_pyvis(graph)
    net.show("nodes.html")
