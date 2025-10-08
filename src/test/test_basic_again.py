import pytest

# the purpose of this is to test the code paths when a module is already built
from .test_basic import incref, max, string, throws, vec


def test_ref() -> None:
    i = 1
    incref(i)  # i is immutable
    assert i == 1


def test_header_required() -> None:
    assert string("string") == 6


def test_stl() -> None:
    assert len(vec(10)) == 10


def test_throws() -> None:
    with pytest.raises(RuntimeError):
        throws()


def test_max() -> None:
    assert max(1, 3) == 3
