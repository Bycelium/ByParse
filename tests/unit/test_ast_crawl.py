from typing import Union, Dict, List

import pytest
import pytest_check as check

import ast
from byparse.ast_crawl import AstContextCrawler


def check_expected_attr_subcontext(
    context: AstContextCrawler,
    expected: Union[List, Dict],
    attr_name: str,
):
    context_attr_name = getattr(context, f"{attr_name}_names")
    context_attr = getattr(context, attr_name)

    if isinstance(expected, list):  # Calls and imports
        check.equal(set(context_attr_name.keys()), set(expected))
    elif isinstance(expected, dict):  # Classes and functions subcontexts
        check.equal(set(context_attr_name.keys()), set(expected))
        for exp, subexp in expected.items():
            check.is_in(exp, context_attr_name)
            if exp in context_attr_name:
                subcontext_ast = context_attr_name[exp]
                subcontext = context_attr[subcontext_ast]
                check_expected_subcontexts(subcontext, subexp)
    else:
        raise TypeError()


def check_expected_subcontexts(context: AstContextCrawler, expected_contexts: dict):
    for attr_name, expected_context in expected_contexts.items():
        check_expected_attr_subcontext(context, expected_context, attr_name)


class TestAstContextCrawler:
    def test_imports_names(self):
        source = "\n".join(
            (
                "import alpha, theta",
                "import beta as b",
                "from gamma import g",
                "",
                "if __name__ == '__main__':",
                "   import delta",
            )
        )

        expected_imports_names = ("alpha", "theta", "b", "g", "delta")

        module_ast = ast.parse(source)
        module = AstContextCrawler(module_ast)
        check.equal(set(module.imports_names.keys()), set(expected_imports_names))

    def test_calls(self):
        source = "\n".join(
            (
                "call_1()",
                "if __name__ == '__main__':",
                "   call_2()",
            )
        )

        expected_call_names = ("call_1", "call_2")

        module_ast = ast.parse(source)
        module = AstContextCrawler(module_ast)
        check.equal(set(module.calls_names.keys()), set(expected_call_names))

    def test_functions_context(self):

        source = "\n".join(
            (
                "def func_1():",
                "   def func_11():",
                "       def func_111():",
                "           pass",
                "   def func_12():",
                "       pass",
                "if __name__ == '__main__':",
                "   def func_2():",
                "       pass",
            )
        )

        expected_contexts = {
            "functions": {
                "func_1": {
                    "functions": {
                        "func_11": {
                            "functions": {"func_111": {}},
                        },
                        "func_12": {},
                    },
                },
                "func_2": {},
            },
        }

        module_ast = ast.parse(source)
        module = AstContextCrawler(module_ast)
        check_expected_subcontexts(module, expected_contexts)

    def test_classes_context(self):

        source = "\n".join(
            (
                "class C1():",
                "   def __init__(self):",
                "       def f1():",
                "           pass",
                "   class C12():",
                "       pass",
                "if __name__ == '__main__':",
                "   class C2():",
                "       pass",
            )
        )
        expected_contexts_calls = {
            "classes": {
                "C1": {
                    "classes": {"C12": {}},
                    "functions": {
                        "__init__": {
                            "functions": {"f1": {}},
                        },
                    },
                },
                "C2": {},
            },
        }

        module_ast = ast.parse(source)
        module = AstContextCrawler(module_ast)
        check_expected_subcontexts(module, expected_contexts_calls)

    def test_context_calls(self):
        source = "\n".join(
            (
                "class C1():",
                "   def __init__(self):",
                "       call_C1_init()",
                "   def meth_1(self):",
                "       def func_C1_1_1():",
                "           call_C1_1_1()",
                "       call_C1_1(self)",
                "       func_C1_1_1()",
                "   def meth_2():",
                "       call_C1_2()",
                "",
                "def func_1():",
                "   def func_1_1():",
                "       call_1_1()",
                "   call_1()",
                "   func_1_1()",
                "",
            )
        )

        expected_contexts_calls = {
            "classes": {
                "C1": {
                    "functions": {
                        "__init__": {
                            "calls": ["call_C1_init"],
                        },
                        "meth_1": {
                            "functions": {
                                "func_C1_1_1": {
                                    "calls": ["call_C1_1_1"],
                                },
                            },
                            "calls": ["call_C1_1", "func_C1_1_1"],
                        },
                        "meth_2": {
                            "calls": ["call_C1_2"],
                        },
                    },
                }
            },
            "functions": {
                "func_1": {
                    "functions": {
                        "func_1_1": {"calls": ["call_1_1"]},
                    },
                    "calls": ["call_1", "func_1_1"],
                },
            },
        }

        module_ast = ast.parse(source)
        module = AstContextCrawler(module_ast)
        check_expected_subcontexts(module, expected_contexts_calls)

    def test_context_imports(self):
        source = "\n".join(
            (
                "class C1():",
                "   def __init__(self):",
                "       import alpha",
                "   def meth_1(self):",
                "       def func_C1_1_1():",
                "           import beta as b",
                "       from gamma import g",
                "       func_C1_1_1()",
                "   def meth_2(self):",
                "       import delta",
                "",
                "def func_1():",
                "   def func_1_1():",
                "       import theta",
                "   func_1_1()",
                "",
            )
        )

        expected_contexts_calls = {
            "classes": {
                "C1": {
                    "functions": {
                        "__init__": {
                            "imports": ["alpha"],
                        },
                        "meth_1": {
                            "functions": {
                                "func_C1_1_1": {
                                    "imports": ["b"],
                                },
                            },
                            "imports": ["g"],
                        },
                        "meth_2": {
                            "imports": ["delta"],
                        },
                    },
                }
            },
            "functions": {
                "func_1": {
                    "functions": {
                        "func_1_1": {"imports": ["theta"]},
                    }
                },
            },
        }

        module_ast = ast.parse(source)
        module = AstContextCrawler(module_ast)
        check_expected_subcontexts(module, expected_contexts_calls)
