import importlib.metadata

__version__ = importlib.metadata.version("inexmo")


from .compile import compile
from .cppmodule import ReturnValuePolicy
from .errors import CompilationError, CppTypeError
from .types import CppQualifier
from .utils import (
    Platform,
    platform_specific,
)

__all__ = [
    "__version__",
    "CompilationError",
    "CppQualifier",
    "CppTypeError",
    "Platform",
    "ReturnValuePolicy",
    "compile",
    "platform_specific",
]
