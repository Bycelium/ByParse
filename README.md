# ByParse

A library to parse python projects and build the graph of all symbolic connexions.

Instead of this:

![toy_project_root](assets/toy_project_root.png)

It ables you to see this:

![toy_graph_image](assets/toy_graph_fcose.png)

# Installation

```bash
pip install git+https://gitea.bycelium.com/vanyle/ByParse.git
```

# Usage

## Produce a graph

```bash
byparse -r path/to/project/root
```

For more details:

```bash
byparse --help
```

## Visualize a graph

### Using cytoscape

See [cytoscape usage](cytovis/README.md).
