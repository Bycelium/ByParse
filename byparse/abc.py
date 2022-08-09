from dataclasses import dataclass
from typing import Set, List


@dataclass
class FileLocation:
    """
    Represents a specific place inside a file
    """

    path: str
    lint: int


@dataclass
class PythonFunctionDefinition:
    """
    Represents a definition of a python function
    """

    name: str
    arguments: List[str]
    path: str  # The file where the function was defined
    line: int
    callingSites: Set[FileLocation]
