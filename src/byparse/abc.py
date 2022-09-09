from enum import Enum, auto


class EdgeType(Enum):
    PATH = auto()
    CONTEXT = auto()
    CALL = auto()
    INHERITANCE = auto()
    TYPEHINT = auto()


class NodeType(Enum):
    FOLDER = auto()
    FILE = auto()
    CLASS = auto()
    FUNCTION = auto()
    LIBRAIRY = auto()
