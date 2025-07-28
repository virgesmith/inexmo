import numpy as np
import numpy.typing as npt

import test_other
from inexmo import Platform, compile, platform_specific

# clang doesnt appear to support -fopenmp without installing deps (libomp)
platform_specific_args: dict[Platform, list[str]] = {
    "Linux": ["-fopenmp"],
    "Windows": ["-fopenmp"],
}


@compile(extra_compile_args=platform_specific(platform_specific_args))
def daxpy(a: float, x: npt.NDArray[float], y: npt.NDArray[float]) -> npt.NDArray[float]:  # type: ignore[empty-body, type-var]
    """
    // Level 1 BLAS - double-precision ax+y modifying y in-place and returning it
    py::buffer_info xbuf = x.request();
    py::buffer_info ybuf = y.request();
    if (xbuf.ndim != 1 || ybuf.ndim != 1)
        throw std::runtime_error("Input arrays must be 1D");
    if (xbuf.shape[0] != ybuf.shape[0])
        throw std::runtime_error("Input arrays must be 1D");

    auto xa = x.unchecked<1>();
    auto ya = y.mutable_unchecked<1>();
    #ifndef __APPLE__
    #pragma omp simd
    #endif
    for (py::ssize_t i = 0; i < xbuf.shape[0]; ++i) {
        ya(i) += a * xa(i);
    }
    return y;
    """


@compile()
def func1(x: int) -> bool:  # type: ignore[empty-body]
    """
    return !(x % 2);
    """


# use auto-vectorisation
@compile(vectorise=True)
def min(a: int, b: int) -> int:  # type: ignore[empty-body]
    """
    return a < b ? a: b;
    """


# hand-code
@compile(extra_compile_args=platform_specific(platform_specific_args))
def max(a: npt.NDArray[int], b: npt.NDArray[int]) -> npt.NDArray[int]:  # type: ignore[empty-body, type-var]
    """
    py::array_t<int> result(std::vector<py::ssize_t>(a.shape(), a.shape() + a.ndim()));

    const int* pa = static_cast<const int*>(a.request().ptr);
    const int* pb = static_cast<const int*>(b.request().ptr);
    int* r = static_cast<int*>(result.request().ptr);

    #ifndef __APPLE__
    #pragma omp simd
    #endif
    for (py::ssize_t i = 0; i < a.size(); ++i)
    {
      r[i] = (pa[i] > pb[i]) ? pa[i] : pb[i];
    }
    return result;
    """


if __name__ == "__main__":
    x = np.ones(10)
    y = np.zeros(10)
    # y is modified in-place and returned
    y_pre_addr = id(y)
    z = daxpy(1, x, y)
    # so y == z
    assert (y == z).all()
    assert y_pre_addr == id(y) and y_pre_addr == id(z)

    print(func1(3))
    print(test_other.func1(3))

    print(func1(4))
    print(test_other.func1(4))
    print(test_other.func2(3.14))

    for i in range(3):
        print(func1(i))

    # a, b = np.array(range(10)), np.array(range(10, 0, -1))

    # print(a.mean(), b.mean(), max(a, b).mean(), min(a, b).mean())

    # print(_module_registry.keys())
