import pytest

from inexmo import compile
from inexmo.utils import get_function_scope


def outer(x: float) -> float:
    @compile()
    def inner(x: float, i: int) -> float:  # type: ignore[empty-body]
        """
        return x * i;
        """

    return inner(x, 5)  # type: ignore[no-any-return]


def test_nested() -> None:
    assert outer(3.1) == 15.5

    from test_nested_ext.test_nested_ext import _outer_inner  # type: ignore[import-not-found]

    assert _outer_inner(2.7, 3) == pytest.approx(8.1)


class Outer:
    class Inner:
        def method(self) -> None:
            pass


def test_get_function_scope() -> None:
    assert get_function_scope(test_nested) == tuple()
    assert get_function_scope(Outer.Inner.method) == ("Outer", "Inner")


if __name__ == "__main__":
    test_nested()
