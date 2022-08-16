import ast
from pathlib import Path

import pytest
import pytest_check as check

from byparse.path_resolvers.calls import (
    get_chain_known_level,
    resolve_call,
    resolve_self_call,
    resolve_import_path_chain,
    resolve_lib_call,
    get_call_chain,
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


class TestGetChainKnownLevel:
    def test_single_chain(self):
        call_name = "func"
        local_used_names = ["func"]
        level = get_chain_known_level(call_name.split("."), local_used_names)
        check.equal(level, 0)

    def test_single_chain_not_found(self):
        call_name = "func"
        local_used_names = []
        level = get_chain_known_level(call_name.split("."), local_used_names)
        check.is_none(level)

    def test_start_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module"]
        level = get_chain_known_level(call_name.split("."), local_used_names)
        check.equal(level, 2)

    def test_middle_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module.Class"]
        level = get_chain_known_level(call_name.split("."), local_used_names)
        check.equal(level, 1)

    def test_middle_only_not_found(self):
        call_name = "module.Class.func"
        local_used_names = ["Class"]
        level = get_chain_known_level(call_name.split("."), local_used_names)
        check.is_none(level)

    def test_end_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module.Class.func"]
        level = get_chain_known_level(call_name.split("."), local_used_names)
        check.equal(level, 0)


class TestGetCallChain:
    def test_single_chain(self):
        call_name = "func"
        local_used_names = ["func"]
        call_chain, call_end, _, _ = get_call_chain(call_name, local_used_names)
        check.equal(call_chain, "func")
        check.equal(call_end, "")

    def test_single_chain_not_found(self):
        call_name = "func"
        local_used_names = []
        call_chain, call_end, _, _ = get_call_chain(call_name, local_used_names)
        check.is_none(call_chain)
        check.is_none(call_end)

    def test_start_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module"]
        call_chain, call_end, _, _ = get_call_chain(call_name, local_used_names)
        check.equal(call_chain, "module")
        check.equal(call_end, "Class.func")

    def test_middle_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module.Class"]
        call_chain, call_end, _, _ = get_call_chain(call_name, local_used_names)
        check.equal(call_chain, "module.Class")
        check.equal(call_end, "func")

    def test_middle_only_not_found(self):
        call_name = "module.Class.func"
        local_used_names = ["Class"]
        call_chain, call_end, _, _ = get_call_chain(call_name, local_used_names)
        check.is_none(call_chain)
        check.is_none(call_end)

    def test_end_chain(self):
        call_name = "module.Class.func"
        local_used_names = ["module.Class.func"]
        call_chain, call_end, _, _ = get_call_chain(call_name, local_used_names)
        check.equal(call_chain, "module.Class.func")
        check.equal(call_end, "")


class TestResolveLibCall:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.call_path = Path(
            "venv", "Lib", "site-packages", "numpy", "core", "__init__.py"
        )

    def test_resolve_lib_call_with_deps(self):

        call_name = "np.array"
        call_path, node_type = resolve_lib_call(
            self.call_path, call_name, with_deps=True
        )

        check.equal(call_path, Path("numpy", "core>array"))
        check.equal(node_type, NodeType.LIBRAIRY.name)

    def test_resolve_lib_call_group_deps(self):
        call_name = "np.array"
        call_path, node_type = resolve_lib_call(
            self.call_path, call_name, with_deps="group"
        )

        check.equal(call_path, Path("numpy"))
        check.equal(node_type, NodeType.LIBRAIRY.name)

    def test_resolve_lib_call_no_deps(self):
        call_name = "np.array"
        call_path, node_type = resolve_lib_call(
            self.call_path, call_name, with_deps=False
        )

        check.is_none(call_path)
        check.equal(node_type, NodeType.LIBRAIRY.name)
