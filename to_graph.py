"""

Read a python package and generate a call graph from it.

To test this, we'll try to analyse scikit learn

"""

import ast
import importlib.util
from pathlib import Path
from os.path import exists
import networkx as nx
from matplotlib import pyplot as plt

path = "toy_project/__main__.py"
G = nx.Graph()
G.add_node(path)

s = ast.parse(source=open(path,"r",encoding="utf8").read(), filename=path)


def package_name_to_path(package_name, filepath):
	"""
		Return the path of the package named <package_name>
		that was imported from the file located at <filepath>
	"""
	spec = None
	try:
		spec = importlib.util.find_spec(package_name, filepath)
	except ModuleNotFoundError as err:
		# This occurs if an import is dependent on code, and is not supposed to be executed on this OS/Machine
		# We cannot know if imports are really executed or not as we're not solving the halting problem.
		# There is no real way to handle this case perfectly
		pass # Might handle this differently?
	if spec is not None:
		if spec.origin == "built-in": return None
		return spec.origin
	else:
		# Try a local resolve based on filepath:
		package_path = Path(filepath).parent / Path(package_name)
		if package_path.exists():
			if package_path.is_dir():
				return package_path / Path("__init__.py")
			else:
				return package_path
	return None # Unable to resolve the package


alreadySeen = set() # infinite recursive safe-guard

def resolveImport(astImportNode, filepath):
	global alreadySeen
	p = Path(filepath).absolute()
	for n in astImportNode.names:
		p = package_name_to_path(n.name, p)

		if p is not None:
			node1 = Path(p).name
			node2 = Path(filepath).name
			G.add_node(node1)
			G.add_edge(node1, node2)

		if p is not None and str(p).endswith(".py"):
			if p in alreadySeen: continue
			alreadySeen.add(p)
			s = ast.parse(source=open(p,"r",encoding="utf8").read(), filename=p)
			exploreTree(s, p)

def exploreTree(s, filepath):
	"""
		Recursive ast tree explorer to extract import statements.
	"""
	# Enumerate the types we can encounter.
	if isinstance(s, ast.Module):
		for i in s.body:
			exploreTree(i,filepath)
	elif isinstance(s, ast.If) or \
		 isinstance(s, ast.For) or \
		 isinstance(s, ast.While) or \
		 isinstance(s, ast.With) or \
		 isinstance(s, ast.ExceptHandler):
		for i in s.body:
			exploreTree(i,filepath)
	elif isinstance(s, ast.FunctionDef):
		for i in s.body:
			exploreTree(i,filepath)
	elif isinstance(s, ast.Try):
		for i in s.body:
			exploreTree(i,filepath)
		for i in s.handlers:
			exploreTree(i,filepath)
		for i in s.finalbody:
			exploreTree(i,filepath)
	elif isinstance(s, ast.Import):
		resolveImport(s, filepath)
	elif isinstance(s, ast.ImportFrom):
		pass
		#print(ast.dump(s))
	else:
		pass
		# Ignore these, they do not contain nested statements
		#print(ast.dump(s))
		#print("-----")
	# print(ast.dump(s.body[5]))

exploreTree(s, path)
# Display the graph generated
nx.draw(G, with_labels = True)
plt.show()