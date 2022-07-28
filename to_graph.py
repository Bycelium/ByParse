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
G = nx.DiGraph()

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
		package_name = package_name.replace(".","./")
		package_path = Path(filepath).parent / Path(package_name)
		if package_path.exists():
			if package_path.is_dir():
				return package_path / Path("__init__.py")
			else:
				return package_path
		else: 
			package_path = Path(str(package_path) + ".py")
			if package_path.exists():
				return package_path
	return None # Unable to resolve the package


alreadySeen = set() # infinite recursive safe-guard

def resolveImport(n, filepath):
	global alreadySeen
	node2 = Path(filepath).name
	p = package_name_to_path(n, str(filepath))

	# print(f"Name: {n}")
	# print(f"	Path: {p}")

	if p is not None:
		node1 = Path(p).name
		G.add_node(node1)
		G.add_edge(node2, node1)
	else:
		node1 = n
		G.add_edge(node2, node1)

	if "lib" in str(p) and "site-packages" not in str(p):
		return # Don't resolve native dependencies to avoid noise in graph

	if p is not None and str(p).endswith(".py"):
		if p in alreadySeen: return
		alreadySeen.add(p)
		try:
			s = ast.parse(source=open(p,"r",encoding="utf8").read(), filename=p)
			exploreTree(s, p)
		except SyntaxError:
			pass # Ignore malformed file.

def exploreTree(s, filepath):
	"""
		Recursive ast tree explorer to extract import statements.
	"""
	fp = Path(filepath).absolute()
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
		for name in s.names:
			resolveImport(name.name, fp)
	elif isinstance(s, ast.ImportFrom):
		for name in s.names:
			module_name = "." + name.name
			if s.module is not None:
				resolveImport(s.module, fp)
				module_name = s.module + "." + name.name

			# Try to import the thing as a whole file, if not just the module name
			# We need to handle both bases:
			# from <big module> import <filename>
			# from <small module> import <specific function>
			resolveImport(module_name, fp)

	else:
		pass
		# Ignore these, they do not contain nested statements
		#print(ast.dump(s))
		#print("-----")
	# print(ast.dump(s.body[5]))

exploreTree(s, path)
# Display the graph generated
pos = nx.spring_layout(G, k=0.5, iterations=30)
nx.draw(G,pos, with_labels = True)
plt.show()