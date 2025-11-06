import importlib.metadata

__version__ = importlib.metadata.version("xenoform")


from .compile import compile
from .cppmodule import ReturnValuePolicy
from .errors import CompilationError, CppTypeError
from .types import CppQualifier
from .utils import (
    Platform,
    platform_specific,
)

__all__ = [
    "CompilationError",
    "CppQualifier",
    "CppTypeError",
    "Platform",
    "ReturnValuePolicy",
    "__version__",
    "compile",
    "platform_specific",
]
