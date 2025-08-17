from typing import Self

import pytest
from other_module import Base, ClassA

from inexmo import compile
from inexmo.utils import get_function_scope


class ClassB(Base):
    X: str = "B"

    def __init__(self) -> None:
        self.x = 2

    @compile()
    def method(self: Self) -> int:  # type: ignore[empty-body]
        """
        // extract instance variable
        return self.attr("x").cast<int>();
        """

    @staticmethod
    @compile()
    def static_method(i: int) -> int:  # type: ignore[empty-body]
        """
        return i + 1000;
        """

    @classmethod
    @compile()
    def class_method(cls: type) -> str:  # type: ignore[empty-body]
        """
        // extract X from cls arg
        auto val = cls.attr("X").cast<std::string>();
        return val;
        """


class ClassC(Base):
    X: str = "C"

    @compile()
    def method(self: Self) -> int:  # type: ignore[empty-body]
        """
        return 3;
        """

    @classmethod
    @compile()
    def class_method(cls: type) -> str:  # type: ignore[empty-body]
        """
        // extract X from cls arg
        auto val = cls.attr("X").cast<std::string>();
        return val;
        """


def test_function_scope() -> None:
    assert get_function_scope(ClassA.method) == ("ClassA",)


def test_methods() -> None:
    a = ClassA()
    b = ClassB()
    c = ClassC()

    def f(obj: Base) -> int:
        return obj.method()

    # test scope resolution works for instance methods
    assert a.method() == f(a) == 1
    assert b.method() == f(b) == 2
    assert c.method() == f(c) == 3

    # test scope resolution works for class methods
    assert a.class_method() == ClassA.class_method() == "A"
    assert b.class_method() == ClassB.class_method() == "B"
    assert c.class_method() == ClassC.class_method() == "C"

    # test static method
    with pytest.raises(AttributeError):
        a.static_method(6)
    assert b.static_method(6) == 1006


if __name__ == "__main__":
    test_methods()
