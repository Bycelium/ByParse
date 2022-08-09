from package import init_package
from package import module1
from package import submodules

def main():
    print(init_package(), module1.m1(), submodules.submodule1.sm1())


if __name__ == "__main__":
    main()
