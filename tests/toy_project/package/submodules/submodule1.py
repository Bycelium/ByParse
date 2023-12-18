import scripts.script1 as s1


def sm1():
    return f"sm1({s1.sc1()})"


class M1:
    def __init__(self) -> None:
        self.var = sm1()

    def m1meth(self):
        return f"m1m({self.var})"
