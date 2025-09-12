import inspect
import sys
from time import sleep
from typing import Annotated

import numpy as np
import numpy.typing as npt

from inexmo import CppQualifier, compile

# Remember most python types are immutable, so they cannot be modified in-place


# @compile(verbose=True)
# # def val_np(vec: Annotated[npt.NDArray[float], CppQualifier.Ref]) -> None:
# def modify_nparray(vec: npt.NDArray[float]) -> None:
#     """
#     // Important: ensure the dtype matches the C++ type, otherwise an implicit copy will be made
#     // and in-place modifications will not persist
#     size_t n = vec.size();
#     auto acc = vec.mutable_unchecked<1>();

#     for (size_t i = 0; i < n; ++i) {
#         acc(i) *= 2;
#     }
#     """


# @compile(verbose=True)
# def modify_list(l: Annotated[list[int], "py::list"]) -> None:
#     """
#     l.append(0);
#     l[py::int_(0)] = 5;
#     """


# @compile(verbose=True)
# def modify_dict(d: Annotated[dict[int, int], "py::dict"]) -> None:
#     """
#     d[py::int_(0)] = 4;
#     d[py::int_(1)] = 2;
#     """


# @compile(verbose=True)
# def modify_set(s: Annotated[set[int], "py::set"]) -> None:
#     """
#     s.add(0);
#     s.add(1);
#     """


# def modify_bytearray(b: Annotated[bytearray, "py::buffer"]) -> None:
@compile(verbose=True)
def modify_bytearray(b: bytearray) -> None:
    """
    b[py::int_(0)] = 4;
    """


def test_inplace_modification() -> None:
    # vec = np.ones(3)
    # modify_nparray(vec)
    # assert (vec == 2.0).all()

    # lst = [1, 2, 3]
    # modify_list(lst)
    # assert lst == [5, 2, 3, 0]

    # dct = {0: 0}
    # modify_dict(dct)
    # assert dct == {0: 4, 1: 2}

    # st = {0}
    # modify_set(st)
    # assert st == {0, 1}

    b = bytearray([0, 1, 2, 3])
    assert "test_memory_ext" not in sys.modules.keys()
    modify_bytearray(b)
    # print([m for m in sys.modules.keys() if "test_memory_ext" in m])

    print(b)
    # assert b == bytearray([7, 1, 2, 3])


if __name__ == "__main__":
    test_inplace_modification()
