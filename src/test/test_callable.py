# can we return a C++ lambda?
from typing import Annotated, Callable

import pytest

from inexmo import compile


@compile()
def function_returning_callable(n: int) -> Callable:  # type: ignore[empty-body, type-arg]
    """
    auto f = [n](int i) { return i % n; };
    return py::cpp_function(f);
    """


@compile()
def function_accepting_callable(f: Annotated[Callable, "py::function"], n: int) -> int:  # type: ignore[empty-body, type-arg]
    """
    // The cast only ensures f returns an int, pybind11 will cast this back to a py::object
    return f(n).cast<int>();
    """


def test_function_returning_callable() -> None:
    f = function_returning_callable(3)

    assert f(0) == 0
    assert f(2) == 2
    assert f(10) == 1
    with pytest.raises(TypeError):
        f("x")
    with pytest.raises(TypeError):
        f()
    with pytest.raises(TypeError):
        f(2, 3)


def test_function_accepting_callable() -> None:
    def f(i: int) -> int:
        return i % 3

    assert function_accepting_callable(lambda i: i % 3, 0) == 0
    assert function_accepting_callable(f, 0) == 0
    assert function_accepting_callable(f, 10) == 1
    assert function_accepting_callable(f, 0) == 0

    with pytest.raises(TypeError):
        function_accepting_callable(f, "x")
    with pytest.raises(TypeError):
        function_accepting_callable(3)
    with pytest.raises(TypeError):
        function_accepting_callable(f, f)


if __name__ == "__main__":
    test_function_returning_callable()
    test_function_accepting_callable()
