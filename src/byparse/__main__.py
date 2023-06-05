import argparse
import json
import os
from pathlib import Path

from byparse.visualisation.graph_vis import (
    color_context_graph,
    compute_parents_and_childs,
)
from byparse.project_crawl import ProjectCrawler
from byparse.logging_utils import init_logger
from byparse.visualisation.cytoscape_fcose import (
    networkx_to_cytoscape_fcose,
    networkx_to_cytoscape_fcose_constraints,
)


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        "-r",
        help="Root directory of the project to parse. Defaults to toy_project.",
        default="tests/integration/toy_project",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output of the html graph.",
        default=None,
    )
    parser.add_argument(
        "--exclude",
        "-x",
        help="Ignored folders.",
        default=None,
    )
    parser.add_argument(
        "--log-level",
        "-v",
        help="Logging level. (DEBUG <= 10, INFO <= 20, WARNING <= 30)",
        default=20,
        type=int,
    )
    return parser.parse_args()


def main():
    args = cli_parser()
    init_logger(log_level=args.log_level, package_name=__package__)
    project = ProjectCrawler(args.root, exclude=args.exclude)
    graph = project.build_contexts_graph()
    graph = project.build_call_graph(graph)

    output = args.output
    if args.output is None:
        output = Path("examples_graphs", f"{Path(args.root).name}.json")
        os.makedirs(output.parent, exist_ok=True)
        output = str(output)

    color_context_graph(graph)
    compute_parents_and_childs(graph)

    cyto_graph = networkx_to_cytoscape_fcose(graph)
    with open(output, "w") as fp:
        json.dump(cyto_graph, fp, indent=2)

    cyto_graph_constraints = networkx_to_cytoscape_fcose_constraints(graph)
    with open(output.split(".")[0] + "_constraints.json", "w") as fp:
        json.dump(cyto_graph_constraints, fp, indent=2)


if __name__ == "__main__":
    main()
