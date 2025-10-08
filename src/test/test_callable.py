# can we return a C++ lambda?

from typing import Callable

import pytest

from inexmo import compile

# @compile()
# def function_returning_cppfunction(n: int) -> CppFunction:  # type: ignore[empty-body]
#     """
#     auto f = [n](int i) { return i % n; };
#     return py::cpp_function(f);
#     """


# @compile()
# def function_accepting_pyfunction(f: PythonFunction, n: int) -> int:  # type: ignore[empty-body]
#     """
#     // The cast only ensures f returns an int, pybind11 will cast this back to a py::object
#     return f(n).cast<int>();
#     """


# @compile()  # extra_includes=["<pybind11/functional.h>"])
# def function_accepting_cppfunction(f: Annotated[CppFunction, "std::function<int(int)>"], i: int) -> int:  # type: ignore[empty-body]
#     """
#     return f(i);
#     """


@compile()
def round_sign() -> Callable[[float, bool], int]:  # type:ignore[empty-body]
    """
    return [](double x, bool s) -> int { return int(s ? -x : x); };
    """


# this is the actual function, not one that returns it
def round_sign_py(x: float, s: bool) -> int:
    return int(-x if s else x)


@compile()
def modulo(n: int) -> Callable[[int], int]:  # type: ignore[empty-body]
    """
    return [n](int i) { return i % n; };
    """


def modulo_py(n: int) -> Callable[[int], int]:
    return lambda i: i % n


@compile()
def use_modulo(f: Callable[[int], int], i: int) -> int:  # type: ignore[empty-body]
    """
    return f(i);
    """


def use_modulo_py(f: Callable[[int], int], i: int) -> int:
    return f(i)


@compile()
def use_round_sign(f: Callable[[float, bool], int], x: float) -> int:  # type:ignore[empty-body]
    """
    return f(x, true);
    """


def use_round_sign_py(f: Callable[[float, bool], int], x: float) -> int:
    return f(x, True)


def test_modulo() -> None:
    f = modulo(3)

    assert f(0) == 0
    assert f(2) == 2
    assert f(10) == 1
    with pytest.raises(TypeError):
        f("x")
    with pytest.raises(TypeError):
        f()
    with pytest.raises(TypeError):
        f(2, 3)

    assert modulo(2)(2) == modulo_py(2)(2) == 0
    assert modulo(3)(3) == modulo_py(3)(3) == 0
    assert modulo(5)(5) == modulo_py(5)(5) == 0
    assert modulo(5)(6) == modulo_py(5)(6) == 1

# TODO test type override

# def test_function_accepting_callable() -> None:
#     def f(i: int) -> int:
#         return i % 3

#     assert function_accepting_pyfunction(lambda i: i % 3, 0) == 0
#     assert function_accepting_pyfunction(f, 0) == 0
#     assert function_accepting_pyfunction(f, 10) == 1
#     assert function_accepting_pyfunction(f, 0) == 0

#     with pytest.raises(TypeError):
#         function_accepting_pyfunction(f, "x")
#     with pytest.raises(TypeError):
#         function_accepting_pyfunction(3)
#     with pytest.raises(TypeError):
#         function_accepting_pyfunction(f, f)


# def test_function_accepting_cpp_callable() -> None:
#     f = function_returning_callable(5)
#     assert function_accepting_cppfunction(f, 7) == 2
#     assert function_accepting_cppfunction(f, 11) == 1
#     assert use_modulo(f, 7) == 2

#     assert use_modulo(lambda n: n % 5, 7) == 2


def test_all_combinations() -> None:
    round_sign_lambda = lambda x, s: int(-x if s else x)  # noqa: E731

    round_sign_cpp = round_sign()

    assert round_sign_py(3.14, False) == round_sign_lambda(3.14, False) == round_sign_cpp(3.14, False) == 3

    assert (
        use_round_sign_py(round_sign_py, 2.72)
        == use_round_sign_py(round_sign_lambda, 2.72)
        == use_round_sign_py(round_sign_cpp, 2.72)
        == -2
    )
    assert (
        use_round_sign(round_sign_py, 2.72)
        == use_round_sign(round_sign_lambda, 2.72)
        == use_round_sign(round_sign_cpp, 2.72)
        == -2
    )


def test_function_type_errors() -> None:
    with pytest.raises(TypeError):
        use_round_sign(modulo, 1.0)
    with pytest.raises(TypeError):
        use_round_sign_py(modulo, 1.0)
    with pytest.raises(TypeError):
        use_round_sign(modulo_py, 1.0)

    with pytest.raises(TypeError):
        use_modulo(round_sign, 1.0)
    with pytest.raises(TypeError):
        use_modulo_py(round_sign, 1.0)
    with pytest.raises(TypeError):
        use_modulo(round_sign_py, 1.0)


if __name__ == "__main__":
    # test_function_returning_callable()
    # test_function_accepting_callable()
    # test_function_accepting_cpp_callable()
    test_all_combinations()
    test_function_type_errors()
