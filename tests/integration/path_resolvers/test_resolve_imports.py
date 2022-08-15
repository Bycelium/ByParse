import ast
from pathlib import Path

import pytest
import pytest_check as check

from byparse.path_resolvers.imports import resolve_import_ast_paths


class TestResolveImportAstPaths:

    """Test cases of resolve_import_ast_paths using toy_project."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.project_root = Path(__file__).parent.parent / Path("toy_project")

    def test_single_package_import(self):
        pkg_alias = ast.alias(name="package")
        import_ast = ast.Import(names=[pkg_alias])

        expected_aliases_paths = {
            pkg_alias: self.project_root / Path("package/__init__.py")
        }

        alias_to_path = resolve_import_ast_paths(import_ast, str(self.project_root))
        check.equal(alias_to_path, expected_aliases_paths)

    def test_multi_import(self):
        pkg_alias = ast.alias(name="package")
        sc1_alias = ast.alias(name="scripts.script1")
        import_ast = ast.Import(names=[pkg_alias, sc1_alias])

        expected_aliases_paths = {
            pkg_alias: self.project_root / Path("package/__init__.py"),
            sc1_alias: self.project_root / Path("scripts/script1.py"),
        }

        alias_to_path = resolve_import_ast_paths(import_ast, str(self.project_root))
        check.equal(alias_to_path, expected_aliases_paths)

    def test_single_package_import_as(self):
        pkg_alias = ast.alias(name="package", asname="pkg")
        import_ast = ast.Import(names=[pkg_alias])

        expected_aliases_paths = {
            pkg_alias: self.project_root / Path("package/__init__.py")
        }

        alias_to_path = resolve_import_ast_paths(import_ast, str(self.project_root))
        check.equal(alias_to_path, expected_aliases_paths)

    def test_single_subpackage_import(self):
        sm_alias = ast.alias(name="package.submodules")
        import_ast = ast.Import(names=[sm_alias])

        expected_aliases_paths = {
            sm_alias: self.project_root / Path("package/submodules/__init__.py")
        }

        alias_to_path = resolve_import_ast_paths(import_ast, str(self.project_root))
        check.equal(alias_to_path, expected_aliases_paths)
