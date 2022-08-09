import random
import string

from dataclasses import dataclass


@dataclass
class UniqueIdentifier:
    """
    A wrapper around a string. Used to indicate that 2 strings are in the same
    context. Used more as a type hint than an actual class.
    """

    v: str


def random_string(l=12):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(l))
