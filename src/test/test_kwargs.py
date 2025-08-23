import pytest

from inexmo import compile

# def f_py(n: int, /, x: float, *, b: bool = False) -> str:
#     return f"{n=} {x=} {b=}"


@compile()
def f_cpp(n: int, /, x: float, y: float = 2.7, *, b: bool = False) -> str:  # type: ignore[empty-body]
    # arg optional positional keyword
    #   n    N         Y         N
    #   x    N         Y         Y
    #   y    Y         Y         Y
    #   b    Y         N         Y
    """
    return "n=" + std::to_string(n) + " x=" + std::to_string(x) + " y=" + std::to_string(y) + " b=" + std::to_string(b);
    """


def test_pos_kwargs() -> None:
    with pytest.raises(TypeError):
        f_cpp(1)
    assert f_cpp(1, 3.1) == "n=1 x=3.100000 y=2.700000 b=0"
    assert f_cpp(1, 3.1, 3.1) == "n=1 x=3.100000 y=3.100000 b=0"
    assert f_cpp(1, x=3.1) == "n=1 x=3.100000 y=2.700000 b=0"
    assert f_cpp(1, x=3.1, y=3.1) == "n=1 x=3.100000 y=3.100000 b=0"
    with pytest.raises(TypeError):
        f_cpp(n=1, x=3.1)
    assert f_cpp(1, 3.1, b=True) == "n=1 x=3.100000 y=2.700000 b=1"
    assert f_cpp(1, b=True, x=2.7) == "n=1 x=2.700000 y=2.700000 b=1"
    with pytest.raises(TypeError):
        f_cpp(1, 3.1, 2.7, True)


if __name__ == "__main__":
    test_pos_kwargs()
