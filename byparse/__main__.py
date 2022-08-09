from byparse import PythonSourceFile

from byparse.visualisation import to_directed_graph, networkx_to_pyvis

root_path = "toy_project/__main__.py"
root_file = PythonSourceFile(path=root_path)

graph = to_directed_graph(root_file)

net = networkx_to_pyvis(graph, "1000px", "600px")
net.show("nodes.html")
