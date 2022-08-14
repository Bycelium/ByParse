from pathlib import Path
import pytest
import pytest_check as check

import json
import networkx as nx
from networkx.readwrite.json_graph import node_link_data, node_link_graph

from byparse.project_crawl import ProjectCrawler


class TestToyProject:
    @pytest.fixture(autouse=True)
    def setup(self):
        toy_project_path = Path(__file__).parent / Path("toy_project")
        self.project = ProjectCrawler(toy_project_path)

    def test_toy_project_context_graph(self):
        expected_graph_dict = {
            "directed": True,
            "multigraph": False,
            "graph": {},
            "nodes": [
                {"label": "module1.py", "type": "FILE", "id": "package\\module1.py"},
                {"label": "package", "type": "FOLDER", "id": "package"},
                {"label": "m1", "type": "FUNCTION", "id": "package\\module1.py>m1"},
                {"label": "m11", "type": "FUNCTION", "id": "package\\module1.py>m11"},
                {"label": "module2.py", "type": "FILE", "id": "package\\module2.py"},
                {"label": "m2", "type": "FUNCTION", "id": "package\\module2.py>m2"},
                {"label": "m22", "type": "FUNCTION", "id": "package\\module2.py>m22"},
                {"label": "__init__.py", "type": "FILE", "id": "package\\__init__.py"},
                {
                    "label": "init_package",
                    "type": "FUNCTION",
                    "id": "package\\__init__.py>init_package",
                },
                {"label": "__main__.py", "type": "FILE", "id": "package\\__main__.py"},
                {
                    "label": "main",
                    "type": "FUNCTION",
                    "id": "package\\__main__.py>main",
                },
                {
                    "label": "submodule1.py",
                    "type": "FILE",
                    "id": "package\\submodules\\submodule1.py",
                },
                {"label": "submodules", "type": "FOLDER", "id": "package\\submodules"},
                {
                    "label": "sm1",
                    "type": "FUNCTION",
                    "id": "package\\submodules\\submodule1.py>sm1",
                },
                {
                    "label": "M1",
                    "type": "CLASS",
                    "id": "package\\submodules\\submodule1.py>M1",
                },
                {
                    "label": "__init__",
                    "type": "FUNCTION",
                    "id": "package\\submodules\\submodule1.py>M1>__init__",
                },
                {
                    "label": "m1meth",
                    "type": "FUNCTION",
                    "id": "package\\submodules\\submodule1.py>M1>m1meth",
                },
                {
                    "label": "submodule2.py",
                    "type": "FILE",
                    "id": "package\\submodules\\submodule2.py",
                },
                {
                    "label": "sm2",
                    "type": "FUNCTION",
                    "id": "package\\submodules\\submodule2.py>sm2",
                },
                {
                    "label": "get_sm2",
                    "type": "FUNCTION",
                    "id": "package\\submodules\\submodule2.py>sm2>get_sm2",
                },
                {
                    "label": "__init__.py",
                    "type": "FILE",
                    "id": "package\\submodules\\__init__.py",
                },
                {"label": "script1.py", "type": "FILE", "id": "scripts\\script1.py"},
                {"label": "scripts", "type": "FOLDER", "id": "scripts"},
                {"label": "sc1", "type": "FUNCTION", "id": "scripts\\script1.py>sc1"},
                {"label": "script2.py", "type": "FILE", "id": "scripts\\script2.py"},
                {"label": "sc2", "type": "FUNCTION", "id": "scripts\\script2.py>sc2"},
                {
                    "label": "subscript1.py",
                    "type": "FILE",
                    "id": "scripts\\subscripts\\subscript1.py",
                },
                {"label": "subscripts", "type": "FOLDER", "id": "scripts\\subscripts"},
                {
                    "label": "sbs1",
                    "type": "FUNCTION",
                    "id": "scripts\\subscripts\\subscript1.py>sbs1",
                },
                {
                    "label": "subscript2.py",
                    "type": "FILE",
                    "id": "scripts\\subscripts\\subscript2.py",
                },
                {
                    "label": "sbs2",
                    "type": "FUNCTION",
                    "id": "scripts\\subscripts\\subscript2.py>sbs2",
                },
            ],
            "links": [
                {"type": "PATH", "source": "package\\module1.py", "target": "package"},
                {
                    "type": "CONTEXT",
                    "source": "package\\module1.py>m1",
                    "target": "package\\module1.py",
                },
                {
                    "type": "CONTEXT",
                    "source": "package\\module1.py>m11",
                    "target": "package\\module1.py",
                },
                {"type": "PATH", "source": "package\\module2.py", "target": "package"},
                {
                    "type": "CONTEXT",
                    "source": "package\\module2.py>m2",
                    "target": "package\\module2.py",
                },
                {
                    "type": "CONTEXT",
                    "source": "package\\module2.py>m22",
                    "target": "package\\module2.py",
                },
                {"type": "PATH", "source": "package\\__init__.py", "target": "package"},
                {
                    "type": "CONTEXT",
                    "source": "package\\__init__.py>init_package",
                    "target": "package\\__init__.py",
                },
                {"type": "PATH", "source": "package\\__main__.py", "target": "package"},
                {
                    "type": "CONTEXT",
                    "source": "package\\__main__.py>main",
                    "target": "package\\__main__.py",
                },
                {
                    "type": "PATH",
                    "source": "package\\submodules\\submodule1.py",
                    "target": "package\\submodules",
                },
                {"type": "PATH", "source": "package\\submodules", "target": "package"},
                {
                    "type": "CONTEXT",
                    "source": "package\\submodules\\submodule1.py>sm1",
                    "target": "package\\submodules\\submodule1.py",
                },
                {
                    "type": "CONTEXT",
                    "source": "package\\submodules\\submodule1.py>M1",
                    "target": "package\\submodules\\submodule1.py",
                },
                {
                    "type": "CONTEXT",
                    "source": "package\\submodules\\submodule1.py>M1>__init__",
                    "target": "package\\submodules\\submodule1.py>M1",
                },
                {
                    "type": "CONTEXT",
                    "source": "package\\submodules\\submodule1.py>M1>m1meth",
                    "target": "package\\submodules\\submodule1.py>M1",
                },
                {
                    "type": "PATH",
                    "source": "package\\submodules\\submodule2.py",
                    "target": "package\\submodules",
                },
                {
                    "type": "CONTEXT",
                    "source": "package\\submodules\\submodule2.py>sm2",
                    "target": "package\\submodules\\submodule2.py",
                },
                {
                    "type": "CONTEXT",
                    "source": "package\\submodules\\submodule2.py>sm2>get_sm2",
                    "target": "package\\submodules\\submodule2.py>sm2",
                },
                {
                    "type": "PATH",
                    "source": "package\\submodules\\__init__.py",
                    "target": "package\\submodules",
                },
                {"type": "PATH", "source": "scripts\\script1.py", "target": "scripts"},
                {
                    "type": "CONTEXT",
                    "source": "scripts\\script1.py>sc1",
                    "target": "scripts\\script1.py",
                },
                {"type": "PATH", "source": "scripts\\script2.py", "target": "scripts"},
                {
                    "type": "CONTEXT",
                    "source": "scripts\\script2.py>sc2",
                    "target": "scripts\\script2.py",
                },
                {
                    "type": "PATH",
                    "source": "scripts\\subscripts\\subscript1.py",
                    "target": "scripts\\subscripts",
                },
                {"type": "PATH", "source": "scripts\\subscripts", "target": "scripts"},
                {
                    "type": "CONTEXT",
                    "source": "scripts\\subscripts\\subscript1.py>sbs1",
                    "target": "scripts\\subscripts\\subscript1.py",
                },
                {
                    "type": "PATH",
                    "source": "scripts\\subscripts\\subscript2.py",
                    "target": "scripts\\subscripts",
                },
                {
                    "type": "CONTEXT",
                    "source": "scripts\\subscripts\\subscript2.py>sbs2",
                    "target": "scripts\\subscripts\\subscript2.py",
                },
            ],
        }
        expected_graph = node_link_graph(expected_graph_dict)
        graph = self.project.build_contexts_graph()
        check.equal(node_link_data(graph), node_link_data(expected_graph))
