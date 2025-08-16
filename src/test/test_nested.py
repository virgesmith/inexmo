import pytest

from inexmo import compile


def outer(x: float) -> float:
    @compile()
    def inner(x: float, i: int) -> float:  # type: ignore[empty-body]
        """
        return x * i;
        """

    return inner(x, 5)  # type: ignore[no-any-return]


def test_nested() -> None:
    assert outer(3.1) == 15.5

    from test_nested_ext.test_nested_ext import inner  # type: ignore[import-not-found]

    assert inner(2.7, 3) == pytest.approx(8.1)


if __name__ == "__main__":
    test_nested()
