from package import init_package
from package import module1 as mod1
from package import submodules

GLOBAL_VAR = 2


def main():
    print(init_package(), mod1.m1(), submodules.submodule1.sm1())


if __name__ == "__main__":
    main()
