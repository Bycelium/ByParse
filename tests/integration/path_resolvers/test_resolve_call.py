import ast
from pathlib import Path

import pytest
import pytest_check as check

from byparse.graphs.call_graph import resolve_call
from byparse.project_crawl import AstContextCrawler
from byparse.abc import NodeType


class TestResolveCallPath:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.project_root = Path(__file__).parent.parent / Path("toy_project")

    def test_call_func_in_module(self):
        call_name = "func"

        source = "\n".join(
            (
                "def func():",
                "   pass",
            )
        )

        module_ast = ast.parse(source=source)
        context = AstContextCrawler(module_ast)
        context_path = self.project_root / Path("context")

        project_modules = {}
        local_used_names = {}
        local_aliases_paths = {}

        call_path, call_type = resolve_call(
            call_name,
            context,
            context_path,
            self.project_root,
            project_modules,
            local_used_names,
            local_aliases_paths,
            with_deps=False,
        )

        check.equal(call_path, "context>func")
        check.equal(call_type, NodeType.FUNCTION.name)

    def test_call_func_in_module(self):
        call_name = "MyClass"

        source = "\n".join(
            (
                "class MyClass():",
                "   pass",
            )
        )

        module_ast = ast.parse(source=source)
        context = AstContextCrawler(module_ast)
        context_path = self.project_root / Path("context")

        project_modules = {}
        local_used_names = {}
        local_aliases_paths = {}

        call_path, call_type = resolve_call(
            call_name,
            context,
            context_path,
            self.project_root,
            project_modules,
            local_used_names,
            local_aliases_paths,
            with_deps=False,
        )

        check.equal(call_path, Path("context>MyClass"))
        check.equal(call_type, NodeType.CLASS.name)
