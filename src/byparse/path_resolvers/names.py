import ast
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple


from byparse.abc import NodeType
from byparse.utils import root_ast_to_node_type, link_path_to_name
from byparse.path_resolvers.imports import (
    resolve_import_ast_alias_path,
    resolve_import_ast_paths,
)
from byparse.logging_utils import get_logger

if TYPE_CHECKING:
    from byparse.context_crawl import AstContextCrawler
    from byparse.project_crawl import ModuleCrawler

LOGGER = get_logger(__name__)


def resolve_same_module_name(
    name: str,
    known_contexts: Dict[str, "AstContextCrawler"],
) -> Tuple[Optional[Path], Optional[NodeType]]:
    call_path = None
    call_type = None
    if name in known_contexts:
        # Function or Class in same file
        other_context = known_contexts[name]
        call_type = root_ast_to_node_type(other_context.root_ast)
        call_path = other_context.path
    return call_path, call_type


def get_call_chain(
    call_name: str,
    local_used_names: List[str],
    chain_level: Optional[int] = None,
):
    call_parts = call_name.split(".")
    if chain_level is None:
        chain_level = get_chain_known_level(call_parts, list(local_used_names))
    if chain_level is not None:
        reverser_call_parts = list(reversed(call_parts))
        call_chain = ".".join(reversed(reverser_call_parts[chain_level:]))
        call_end = ".".join(reversed(reverser_call_parts[:chain_level]))
        return call_chain, call_end, call_parts, chain_level
    else:
        return None, None, call_parts, None


def get_chain_known_level(call_parts: List[str], local_used_names: List[str]):
    reversed_call_parts = list(reversed(call_parts))
    for level in range(len(reversed_call_parts)):
        # Look for part of module chain in local used names in decreasing lenght of chain
        call_chain = ".".join(reversed(reversed_call_parts[level:]))
        if call_chain in local_used_names:
            return level


def resolve_lib_name(
    call_true_path: Path, call_name: str, with_deps=False
) -> Tuple[Optional[Path], NodeType]:
    node_type = NodeType.LIBRAIRY.name

    if not with_deps:
        return None, node_type

    if "__init__.py" in call_true_path.parts or "__main__.py" in call_true_path.parts:
        call_true_path = call_true_path.parent

    try:
        lib_index = call_true_path.parts.index("site-packages")
    except ValueError:
        lib_index = call_true_path.parts.index("lib")
    call_true_path = Path(*call_true_path.parts[lib_index + 1 :])
    if with_deps == "group":
        call_path = Path(call_true_path.parts[0])
    else:
        call_end = call_name.split(".")[-1]
        call_path = link_path_to_name(call_true_path, call_end)

    return Path(call_path), node_type


def resolve_import_path_chain(
    call_name: str,
    project_modules: Dict[Path, "ModuleCrawler"],
    alias_name: str,
    call_end: str,
    call_true_path: Path,
    project_path: Path,
):
    target: "ModuleCrawler" = project_modules[
        call_true_path.absolute().relative_to(project_path.absolute())
    ]

    while (
        alias_name not in target.context.known_names
        and call_end not in target.context.known_names
    ):
        # Solve chained imports until reaching the functions / class definition
        if alias_name in target.context.imports:
            import_from_ast = target.context.imports[alias_name]
        elif call_end in target.context.imports:
            import_from_ast = target.context.imports[call_end]
        else:
            known_names = str(list(target.context.known_names.keys()))
            import_names = str(list(target.context.imports.keys()))
            LOGGER.debug(
                "Could not resolve call_chain %s: %s & %s not found in"
                " known_names:%s nor in imports_names:%s",
                call_name,
                alias_name,
                call_end,
                known_names,
                import_names,
            )
            return None, None

        target_path = resolve_import_ast_paths(import_from_ast, str(target.root))
        target_path = list(target_path.values())[0]
        target = project_modules[
            target_path.absolute().relative_to(target.root.absolute())
        ]
        call_true_path = target_path



    if alias_name in target.context.functions or call_end in target.context.functions:
        call_type = NodeType.FUNCTION.name
    elif alias_name in target.context.classes or call_end in target.context.classes:
        call_type = NodeType.CLASS.name

    call_path = Path(link_path_to_name(call_true_path, call_name.split(".")[-1]))
    return call_path, call_type


def resolve_name(
    name: str,
    context_path: Path,
    project_path: Path,
    project_modules: Dict[Path, "ModuleCrawler"],
    local_known_contexts: Dict[str, "AstContextCrawler"],
    local_used_names: Dict[str, "ast.alias"],
    local_aliases_paths: Dict["ast.alias", Path],
    with_deps=False,
) -> Tuple[Optional[Path], NodeType]:
    name_path, name_type = resolve_same_module_name(name, local_known_contexts)
    if name_path is not None:
        return name_path.relative_to(project_path), name_type

    chain, end, _, chain_level = get_call_chain(name, list(local_used_names.keys()))

    if chain in local_used_names:
        # Function or Class imported
        alias: ast.alias = local_used_names[chain]
        name_true_path: Path = local_aliases_paths[alias]

        # Filter libs
        if "site-packages" in name_true_path.parts or "lib" in name_true_path.parts:
            return resolve_lib_name(name_true_path, name, with_deps)

        name_path, name_type = resolve_import_path_chain(
            name,
            project_modules,
            alias.name,
            end,
            name_true_path,
            project_path,
        )
        if name_path is not None:
            return name_path.relative_to(project_path), name_type
        else:
            # Try with other call_parts
            level = chain_level - 1
            while name_path is None and level >= 0:
                chain, end, _, chain_level = get_call_chain(
                    name, list(local_used_names.keys()), level
                )

                rel_context_path = context_path.relative_to(project_path)
                if (
                    "__main__.py" in rel_context_path.parts
                    or "__init__.py" in rel_context_path.parts
                ):
                    rel_context_path = rel_context_path.parent

                full_name = ".".join(list(rel_context_path.parts) + [chain])
                alias: ast.alias = ast.alias(name=full_name)

                name_true_path: Path = resolve_import_ast_alias_path(
                    alias, project_path
                )

                name_path, name_type = resolve_import_path_chain(
                    name,
                    project_modules,
                    alias.name,
                    end,
                    name_true_path,
                    project_path,
                )
                level -= 1

            if name_path is not None:
                return name_path.relative_to(project_path), name_type

    return None, None
