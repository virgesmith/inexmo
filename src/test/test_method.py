from typing import Self

# testing not interference with class with same name in different module
import other_x

from inexmo import compile


class X:
    Y: int = 5
    Z: int = 6

    def __init__(self) -> None:
        self.x = 1

    @compile()
    def method(self: Self) -> int:  # type: ignore[empty-body]
        """
        // extract instance variable
        auto x = self.attr("x").cast<int>() + 10;
        // reassign
        self.attr("x") = x;
        return x;
        """

    @staticmethod
    @compile()
    def static_method() -> int:  # type: ignore[empty-body]
        """
        // need to jump through hoops...
        auto cls = py::module::import("test_method").attr("X");
        // extract class variable
        int z = cls.attr("Z").cast<int>() + 1000;
        cls.attr("Z") = z;
        return z;
        """

    @classmethod
    @compile()
    def class_method(cls: type) -> int:  # type: ignore[empty-body]
        """
        // extract Y (easier as we have class already)
        auto y = cls.attr("Y").cast<int>() + 100;
        cls.attr("Y") = y;
        return y;
        """


def test_methods() -> None:
    x = X()
    assert x.method() == x.x
    assert X.class_method() == X.Y == 105
    assert X.static_method() == X.Z == 1006

    assert other_x.X.class_method() == "X"


if __name__ == "__main__":
    test_methods()
