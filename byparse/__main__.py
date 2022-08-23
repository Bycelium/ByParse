import argparse
import json
from logging import DEBUG
import os
from pathlib import Path

from byparse.visualisation import networkx_to_pyvis, color_context_graph
from byparse.project_crawl import ProjectCrawler
from byparse.logging_utils import init_logger
from byparse.visualisation.cytoscape_fcose import networkx_to_cytoscape_fcose


def cli_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        "-r",
        help="Root directory of the project to parse.",
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
    return parser.parse_args()


def main():
    args = cli_parser()
    init_logger(log_level=DEBUG, package_name=__package__)
    project = ProjectCrawler(args.root, exclude=args.exclude)
    graph = project.build_contexts_graph()
    graph = project.build_call_graph(graph)

    output = args.output
    if args.output is None:
        output = Path("examples_graphs", f"{Path(args.root).name}.json")
        os.makedirs(output.parent, exist_ok=True)
        output = str(output)

    color_context_graph(graph)
    with open(output, "w") as fp:
        cyto_graph = networkx_to_cytoscape_fcose(graph)
        json.dump(cyto_graph, fp, indent=2)


if __name__ == "__main__":
    main()
