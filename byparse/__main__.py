import argparse
from logging import DEBUG

from byparse.visualisation import networkx_to_pyvis, color_context_graph
from byparse.project_crawl import ProjectCrawler
from byparse.logging_utils import init_logger


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
        default="nodes.html",
    )
    return parser.parse_args()


def main():
    args = cli_parser()
    init_logger(log_level=DEBUG, package_name=__package__)
    project = ProjectCrawler(args.root)
    graph = project.build_contexts_graph()
    graph = project.build_call_graph(graph)
    color_context_graph(graph)

    net = networkx_to_pyvis(graph)
    net.toggle_physics(True)
    net.show(args.output)


if __name__ == "__main__":
    main()
