from pathlib import Path


def pretty_path_name(path: Path):
    name = path.name
    if name in ("__init__.py", "__main__.py"):
        suffix = path.name[:-3].replace("_", "")
        name = f"{path.parent.name}({suffix})"
    return name
