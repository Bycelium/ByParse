import scripts.subscripts.subscript1
from scripts.subscripts.subscript2 import sbs2


def sc1():
    return f"sc1({scripts.subscripts.subscript1.sbs1()}, {sbs2()})"
