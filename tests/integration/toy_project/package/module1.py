from package.submodules.submodule1 import sm1, M1


def m1(y: "M11"):
    return f"m1({(sm1())}, {m11()}, {y})"


class M11(M1):
    def __str__(self) -> str:
        return self.m1meth()

    __repr__ = __str__


def m11(y: M11):
    x = M1()
    return f"m11({x.m1meth()}, {y.m1meth()})"
