from contextlib import redirect_stdout
from io import StringIO

from inexmo import compile


@compile(verbose=True)
def f() -> int:  # type: ignore[empty-body]
    """
    return 42;
    """


@compile(verbose=True)
def g() -> str:  # type: ignore[empty-body]
    """
    return "hello";
    """


def test_cacheing() -> None:
    buf = StringIO()
    with redirect_stdout(buf):
        try:
            print(f(), g())
            print(f())
        except:
            raise

    stdout = buf.getvalue().splitlines()
    # each of these should appear only once:
    for log in (
        "importing compiled module test_caching",
        "retrieved compiled function test_caching._f",
        "retrieved compiled function test_caching._g",
    ):
        assert sum(1 for line in stdout if log in line) == 1

    # C++ functions are now directly bound to the above, there should be no logging output
    assert stdout[-2] == "42 hello"
    assert stdout[-1] == "42"


if __name__ == "__main__":
    test_cacheing()
