import importlib.metadata

__version__ = importlib.metadata.version("inexmo")


from .compile import compile
from .errors import CompilationError, CppTypeError
from .utils import (
    Platform,
    platform_specific,
)

__all__ = [
    "__version__",
    "CompilationError",
    "CppTypeError",
    "Platform",
    "compile",
    "platform_specific",
]
