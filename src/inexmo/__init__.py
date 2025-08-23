import importlib.metadata

__version__ = importlib.metadata.version("inexmo")


from .compile import compile
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
    "compile",
    "platform_specific",
]
