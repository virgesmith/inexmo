from inexmo import compile
from inexmo.compile import _get_function

docstr = """This is a test function
used to test the help system
It is otherwise useless
"""


@compile(help=docstr, debug=True)
def documented_function(n: int, *, x: float = 3.1) -> float:  # type: ignore[empty-body]
    """
    return n + x;
    """


def test_documented_function() -> None:
    assert documented_function.__doc__ == docstr
    # access pybind11 module directly
    ext_func = _get_function("test_help", "_documented_function")
    assert docstr in ext_func.__doc__


if __name__ == "__main__":
    test_documented_function()
