from byparse import PythonSourceFile

from byparse.visualisation import to_directed_graph, networkx_to_pyvis


if __name__ == "__main__":
    filepath = "toy_project/package/__main__.py"
    cwd_of_user = "toy_project"

    root_file = PythonSourceFile(filepath=filepath, user_cwd=cwd_of_user)

    graph = to_directed_graph(root_file)

    net = networkx_to_pyvis(graph, "1000px", "600px")
    net.show("nodes.html")
