from byparse import PythonSourceFile

from byparse.visualisation import to_directed_graph, networkx_to_pyvis
from byparse.ast_crawl import parse_project, pretty_print_ast_elements

if __name__ == "__main__":
    # filepath = "toy_project/package/__main__.py"
    # cwd_of_user = "toy_project"

    # root_file = PythonSourceFile(filepath=filepath, user_cwd=cwd_of_user)

    # graph = to_directed_graph(root_file)

    # net = networkx_to_pyvis(graph)
    # net.show("nodes.html")

    project_root = "toy_project"
    module_asts = parse_project(project_root)
    pretty_print_ast_elements(module_asts)
