import ast
from pathlib import Path

import pytest
import pytest_check as check

from byparse.path_resolvers.calls import (
    resolve_call,
    resolve_self_call,
    resolve_import_path_chain,
    resolve_lib_call,
    get_local_known_chain,
)
from byparse.project_crawl import AstContextCrawler
from byparse.abc import NodeType


class TestResolveCallPath:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.project_root = Path(__file__).parent.parent / Path("toy_project")

    def test_resolve_self_call_func(self):
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

        call_path, call_type = resolve_self_call(call_name, context, context_path)

        check.equal(call_path.relative_to(self.project_root), Path("context>func"))
        check.equal(call_type, NodeType.FUNCTION.name)

    def test_resolve_self_call_class(self):
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

        call_path, call_type = resolve_self_call(call_name, context, context_path)

        check.equal(call_path.relative_to(self.project_root), Path("context>MyClass"))
        check.equal(call_type, NodeType.CLASS.name)


class TestGetLocalChain:
    def test_single_chain(self):
        call_name = "func"
        local_used_names = ["func"]
        call_chain, call_end = get_local_known_chain(call_name, local_used_names)
        check.equal(call_chain, "func")
        check.equal(call_end, "")

    def test_single_chain_not_found(self):
        call_name = "func"
        local_used_names = []
        call_chain, call_end = get_local_known_chain(call_name, local_used_names)
        check.is_none(call_chain)
        check.is_none(call_end)

    def test_start_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module"]
        call_chain, call_end = get_local_known_chain(call_name, local_used_names)
        check.equal(call_chain, "module")
        check.equal(call_end, "Class.func")

    def test_middle_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module.Class"]
        call_chain, call_end = get_local_known_chain(call_name, local_used_names)
        check.equal(call_chain, "module.Class")
        check.equal(call_end, "func")

    def test_middle_only_not_found(self):
        call_name = "module.Class.func"
        local_used_names = ["Class"]
        call_chain, call_end = get_local_known_chain(call_name, local_used_names)
        check.is_none(call_chain)
        check.is_none(call_end)

    def test_end_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module.Class.func"]
        call_chain, call_end = get_local_known_chain(call_name, local_used_names)
        check.equal(call_chain, "module.Class.func")
        check.equal(call_end, "")
