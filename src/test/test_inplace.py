from typing import Annotated

import numpy as np
import numpy.typing as npt

from inexmo import compile

# Remember most python types are immutable, so they cannot be modified in-place


@compile()
def modify_nparray(vec: npt.NDArray[np.float64]) -> None:
    """
    // Important: ensure the dtype matches the C++ type, otherwise an implicit copy will be made
    // and in-place modifications will not persist
    size_t n = vec.size();
    auto acc = vec.mutable_unchecked<1>();

    for (size_t i = 0; i < n; ++i) {
        acc(i) *= 2;
    }
    """


@compile()
def modify_list(lst: Annotated[list[int], "py::list"]) -> None:
    """
    lst.append(0);
    lst[py::int_(0)] = 5;
    """


@compile()
def modify_dict(d: Annotated[dict[int, int], "py::dict"]) -> None:
    """
    d[py::int_(0)] = 4;
    d[py::int_(1)] = 2;
    """


@compile()
def modify_set(s: Annotated[set[int], "py::set"]) -> None:
    """
    s.add(0);
    s.add(1);
    """


@compile()
def modify_bytearray(b: bytearray) -> None:
    """
    b[py::int_(0)] = 5;
    """


def test_inplace_modification() -> None:
    vec = np.ones(3)
    modify_nparray(vec)
    assert (vec == 2.0).all()

    lst = [1, 2, 3]
    modify_list(lst)
    assert lst == [5, 2, 3, 0]

    dct = {0: 0}
    modify_dict(dct)
    assert dct == {0: 4, 1: 2}

    st = {0}
    modify_set(st)
    assert st == {0, 1}

    b = bytearray([0, 1, 2, 3])
    modify_bytearray(b)


if __name__ == "__main__":
    test_inplace_modification()
