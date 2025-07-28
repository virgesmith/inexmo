from inexmo.compile import compile


@compile()
def func1(x: int) -> bool:  # type: ignore[empty-body]
    """
    return (x % 2);
    """


@compile()
def func2(x: float) -> float:  # type: ignore[empty-body]
    """
    return x - static_cast<int>(x);
    """
