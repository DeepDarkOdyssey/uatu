import hashlib
import os
from typing import Union


def id_generator(len: int = 8, salt: str = "test") -> str:
    seed = bytes(salt, encoding="ascii") + os.urandom(16)
    return hashlib.md5(seed).hexdigest()[:len]


def get_relative_path(path: str, cwd: str = os.getcwd()) -> str:
    if not path.startswith("/") and not path.startswith("./"):
        return path
    else:
        return os.path.relpath(path, cwd)


def check_file_exists(file_path: str) -> bool:
    pass
