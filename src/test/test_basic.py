import platform
from typing import Annotated

import pytest

from inexmo import CompilationError, CppTypeError, Platform, platform_specific
from inexmo.compile import FunctionSpec, ModuleSpec, _build_module_impl, _parse_macros, compile
from inexmo.types import CppQualifier
from inexmo.utils import translate_function_signature


def test_signature_translation() -> None:
    def f(_i: int) -> None:
        ""

    assert translate_function_signature(f) == ("[](int _i) -> void", set())

    def f2(a: float, b: str, c: bool) -> int:  # type: ignore[empty-body]
        ""

    assert translate_function_signature(f2) == ("[](double a, std::string b, bool c) -> int", {"<string>"})

    def f3(a: float, b: Annotated[str, CppQualifier.CRef], c: bool) -> int:  # type: ignore[empty-body]
        ""

    assert translate_function_signature(f3) == ("[](double a, const std::string& b, bool c) -> int", {"<string>"})

    def f4(a: float, b: Annotated[str, "const char*"], c: bool) -> int:  # type: ignore[empty-body]
        ""

    assert translate_function_signature(f4) == ("[](double a, const char* b, bool c) -> int", set())


def test_platform_specific() -> None:
    assert platform_specific({}) is None

    settings: dict[Platform, list[str]] = {
        "Linux": ["linux"],
        "Darwin": ["darwin"],
        "Windows": ["windows"],
    }

    assert platform_specific(settings) == [platform.system().lower()]
    del settings["Darwin"]
    assert platform_specific(settings) == ([platform.system().lower()] if platform.system() != "Darwin" else None)


def test_parse_macros() -> None:
    assert _parse_macros(set()) == {}
    assert _parse_macros({"NDEBUG"}) == {"NDEBUG": None}
    assert _parse_macros({"VER=3"}) == {"VER": "3"}
    assert _parse_macros({"NDEBUG", "VER=3"}) == {"NDEBUG": None, "VER": "3"}


@compile()
def max(i: int, j: int) -> int:  # type: ignore[empty-body]
    "return i > j ? i : j;"


def test_basic() -> None:
    assert max(2, 3) == 3


@compile()
def incref(i: Annotated[int, CppQualifier.Ref]) -> None:
    """
    ++i;
    """


def test_ref() -> None:
    i = 1
    incref(i)  # i is immutable
    assert i == 1


@compile()
def string(s: str) -> int:  # type: ignore[empty-body]
    """
    return s.size();
    """


def test_header_required() -> None:
    assert string("string") == 6


@compile(extra_headers=["<pybind11/stl.h>"], define_macros=["PYBIND11_DETAILED_ERROR_MESSAGES"])
def vec(size: int) -> list[int]:  # type: ignore[empty-body]
    """
    return std::vector<int>(size);
    """


def test_stl() -> None:
    assert len(vec(10)) == 10


@compile()
def throws() -> bool:  # type: ignore[empty-body]
    """
    throw std::runtime_error("oops");
    """


def test_throws() -> None:
    with pytest.raises(RuntimeError):
        throws()


def test_unknown_type() -> None:
    with pytest.raises(CppTypeError):

        class X: ...

        @compile()
        def unknown(x: X) -> bool:  # type: ignore[empty-body]
            "return false;"


def test_compile_error() -> None:
    f = """{
#error
}"""
    spec = ModuleSpec().add_function(FunctionSpec(name="error", body=f, scope=tuple()))
    with pytest.raises(CompilationError):
        _build_module_impl("broken_module", spec)
