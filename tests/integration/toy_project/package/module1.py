from package.submodules.submodule1 import sm1, M1


def m1():
    return f"m1({(sm1())}, {m11()})"


def m11():
    x = M1()
    return f"m11({x.m1meth()})"
