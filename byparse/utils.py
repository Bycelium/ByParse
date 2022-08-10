from pathlib import Path


def try_open_python_file(filepath: Path) -> str:
    if filepath.suffix != ".py":
        raise OSError(f"File is not a python file: {filepath}.")
    return open(filepath, "r", encoding="utf8").read()
