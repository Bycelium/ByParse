from package.submodules.submodule2 import sm2


def m2():
    return f"m2({(sm2())})"


def m22():
    from package.submodules.submodule1 import s1

    return f"m22({s1.sbs2()})"
