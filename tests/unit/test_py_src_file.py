from pathlib import Path

import pytest_check as check

from byparse.py_src_file import package_name_to_path


def test_package_name_to_path():
    """
    Usage example for package_name_to_path.
    """
    numpy = package_name_to_path("numpy", ".")
    check.is_true(numpy.endswith(str(Path("lib/site-packages/numpy/__init__.py"))))

    utils = package_name_to_path("utils", "./toy_project/__main__.py")
    check.is_true(utils.endswith(str(Path("utils/__init__.py"))))

    pyplot = package_name_to_path("matplotlib.pyplot", ".")
    check.is_true(pyplot.endswith(str(Path("lib/site-packages/matplotlib/pyplot.py"))))

    doesnotexist = package_name_to_path("doesnotexist", "./toy_project/__main__.py")
    check.is_true(doesnotexist is None)
