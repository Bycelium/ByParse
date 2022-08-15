import ast
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Tuple, Union


from byparse.abc import NodeType
from byparse.utils import root_ast_to_node_type, link_path_to_name
from byparse.path_resolvers.imports import resolve_import_ast_paths
from byparse.logging_utils import get_logger

if TYPE_CHECKING:
    from byparse.context_crawl import AstContextCrawler
    from byparse.project_crawl import ModuleCrawler

LOGGER = get_logger(__name__)


def resolve_call(
    call_name: str,
    context: "AstContextCrawler",
    context_path: Path,
    project_path: Path,
    project_modules: Dict[Path, "ModuleCrawler"],
    local_used_names: Dict[str, "ast.alias"],
    local_aliases_paths: Dict["ast.alias", Path],
    with_deps=False,
) -> Tuple[Union[Path, str, None], NodeType]:
    call_parts = call_name.split(".")

    call_path = None
    if call_name in context.known_names:
        # Function or Class in same file
        other_context = context.known_names[call_name]
        call_type = root_ast_to_node_type(other_context.root_ast)
        call_path = Path(link_path_to_name(context_path, other_context.root_ast.name))
        return str(call_path.relative_to(project_path)), call_type

    level = 0
    call_chain = call_name
    call_end = ""
    while call_chain not in local_used_names and level < len(call_parts):
        # Look for part of module chain in local used names in decreasing lenght of chain
        call_chain = ".".join(call_parts[: 1 - level])
        call_end = ".".join(call_parts[1 - level :])
        level += 1

    if call_chain in local_used_names:
        # Function or Class imported
        alias: ast.alias = local_used_names[call_chain]
        call_true_path: Path = local_aliases_paths[alias]

        # Filter libs
        if "lib" in call_true_path.parts:
            if not with_deps:
                return None, NodeType.LIBRAIRY.name
            if (
                "__init__.py" in call_true_path.parts
                or "__main__.py" in call_true_path.parts
            ):
                call_true_path = call_true_path.parent
            call_true_path = call_true_path.parts[-1].split(".py")[0]
            if with_deps == "group":
                call_path = call_true_path
            else:
                call_path = link_path_to_name(call_true_path, call_parts[-1])
            return call_path, NodeType.LIBRAIRY.name

        target: "ModuleCrawler" = project_modules[
            call_true_path.relative_to(project_path)
        ]

        while (
            alias.name not in target.context.known_names
            and call_end not in target.context.known_names
        ):
            # Solve chained imports until reaching the functions / class definition
            if alias.name in target.context.imports:
                import_from_ast = target.context.imports[alias.name]
            elif call_end in target.context.imports:
                import_from_ast = target.context.imports[call_end]
            else:
                known_names = str(list(target.context.known_names.keys()))
                import_names = str(list(target.context.imports.keys()))
                LOGGER.debug(
                    "Could not resolve call_chain %s: %s & %s not found in"
                    " known_names:%s nor in imports_names:%s",
                    call_name,
                    alias.name,
                    call_end,
                    known_names,
                    import_names,
                )
                return None, None

            target_path = resolve_import_ast_paths(import_from_ast, str(target.root))
            target_path = list(target_path.values())[0]
            target = project_modules[target_path.relative_to(target.root)]
            call_true_path = target_path

        if (
            alias.name in target.context.functions
            or call_end in target.context.functions
        ):
            call_type = NodeType.FUNCTION.name
        elif alias.name in target.context.classes or call_end in target.context.classes:
            call_type = NodeType.CLASS.name

        return link_path_to_name(call_true_path, call_parts[-1]), call_type

    return None, None
