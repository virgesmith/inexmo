import inspect
import platform
from typing import Any, Callable, Literal, cast

from inexmo.types import header_requirements, translate_type

Platform = Literal["Linux", "Darwin", "Windows"]
Platforms = list[Platform] | None


def platform_specific(settings: dict[Platform, list[str]]) -> list[str] | None:
    """
    Given a dict of possible platform-specific settings, return the appropriate values, if set
    """
    return settings.get(cast(Platform, platform.system()))


def _translate_type(value: Any) -> str:
    translations = {"False": "false", "True": "true"}
    return translations.get(str(value), str(value))


def translate_function_signature(func: Callable[..., Any]) -> tuple[str, list[str], list[str]]:
    "map python signature to C++ equivalent"
    arg_spec = inspect.getfullargspec(func)

    headers = []
    arg_defs = []
    arg_annotations = []

    # parse signature - get defaults and positions of pos-only and kw-only
    sig = inspect.signature(func)
    raw_sig = str(sig).replace(" ", "").split(",")
    pos_only = raw_sig.index("/") if "/" in raw_sig else None
    kw_only = raw_sig.index("*") if "*" in raw_sig else None
    defaults = {k: v.default for k, v in sig.parameters.items() if v.default is not inspect.Parameter.empty}

    ret: str | None = None
    for var_name, type_ in arg_spec.annotations.items():
        cpptype = translate_type(type_)
        headers.extend(cpptype.headers(header_requirements))
        if var_name == "return":
            ret = str(cpptype)
        else:
            arg_def = f"{cpptype} {var_name}"
            arg_annotation = f'py::arg("{var_name}")'
            if var_name in defaults:
                arg_def += f"={_translate_type(defaults[var_name])}"
                arg_annotation += f"={_translate_type(defaults[var_name])}"
            arg_defs.append(arg_def)
            arg_annotations.append(arg_annotation)
    if pos_only:
        arg_annotations.insert(pos_only, "py::pos_only()")
    if kw_only:
        arg_annotations.insert(kw_only, "py::kw_only()")
    # print(arg_defs)
    # print(arg_annotations)
    return f"[]({', '.join(arg_defs)})" + (f" -> {ret}" if ret else ""), arg_annotations, headers


def get_function_scope(func: Callable[..., Any]) -> tuple[str, ...]:
    """
    Returns the name of the class for class and instance methods
    NB Does not work for static methods
    """
    return tuple(s for s in func.__qualname__.split(".")[:-1] if s != "<locals>")
