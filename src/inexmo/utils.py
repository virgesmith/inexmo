import platform
from inspect import getfullargspec
from typing import Any, Callable, Literal, cast

from inexmo.types import header_requirements, translate_type

Platform = Literal["Linux", "Darwin", "Windows"]
Platforms = list[Platform] | None


def platform_specific(settings: dict[Platform, list[str]]) -> list[str] | None:
    """
    Given a dict of possible platform-specific settings, return the appropriate values, if set
    """
    return settings.get(cast(Platform, platform.system()))


def translate_function_signature(func: Callable[..., Any]) -> tuple[str, set[str]]:
    "map python signature to C++ equivalent"
    arg_spec = getfullargspec(func)

    headers = set()

    args = []
    ret: str | None = None
    for var_name, type_ in arg_spec.annotations.items():
        cpptype = translate_type(type_)
        headers |= cpptype.headers(header_requirements)
        if var_name == "return":
            ret = str(cpptype)
        else:
            args.append(f"{cpptype} {var_name}")
    return f"[]({', '.join(args)})" + (f" -> {ret}" if ret else ""), headers


def get_function_scope(func: Callable[..., Any]) -> tuple[str, ...]:
    """
    Returns the name of the class for class and instance methods
    NB Does not work for static methods
    """
    return tuple(s for s in func.__qualname__.split(".")[:-1] if s != "<locals>")
