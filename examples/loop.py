from time import process_time

import numpy as np
import numpy.typing as npt
import pandas as pd

from inexmo import compile

rng = np.random.default_rng(19937)

rate = 0.001


# pybind11 cannot directly deal with pandas objects, but internally they are numpy arrays
@compile()
def calc_balances_cpp(data: npt.NDArray[int], rate: float, result: npt.NDArray[float]) -> None:  # type: ignore[type-var]
    """
    py::buffer_info dbuf = data.request();
    py::buffer_info rbuf = result.request();
    if (dbuf.ndim != 1 || rbuf.ndim != 1)
        throw std::runtime_error("Input and output arrays must be 1D");

    py::ssize_t n = dbuf.shape[0];
    if (rbuf.shape[0] != n)
        throw std::runtime_error("Input and output arrays must have same length");

    auto d = data.unchecked<1>();
    auto r = result.mutable_unchecked<1>();

    double current_value = 0.0;
    for (py::ssize_t i = 0; i < n; ++i) {
        current_value = (current_value + d(i)) * (1.0 - rate);
        r(i) = current_value;
    }
    """


def calc_balances_py(data: pd.Series, rate: float) -> pd.Series:
    """Cannot vectorise, since each value is dependent on the previous value"""
    results = []
    current_value = 0.0
    for _, value in data.items():
        current_value = (current_value + value) * (1 - rate)
        results.append(current_value)
    return pd.Series(index=data.index, data=results)  # type: ignore[no-any-return]


def main() -> None:
    """Run a performance comparison for varying series lengths"""
    print("N | py (ms) | cpp (ms) | speedup (%)")
    print("--|---------|----------|------------")
    for N in [1000, 10000, 100000, 1000000, 10000000]:
        data = pd.Series(index=range(N), data=rng.integers(-100, 101, size=N), name="cashflow")

        start = process_time()
        py_result = calc_balances_py(data, rate)
        py_time = process_time() - start

        start = process_time()
        # Although we can actually construct a pd.Series in C++, it is simpler to create it in python
        # and pass it to be interpreted as a numpy array. For fairness, this allocation is included in the C++ time
        cpp_result = pd.Series(index=data.index)
        calc_balances_cpp(data, rate, cpp_result)
        cpp_time = process_time() - start

        print(f"{N} | {py_time * 1000:.1f} | {cpp_time * 1000:.1f} | {100 * (py_time / cpp_time - 1.0):.0f}")
        assert py_result.equals(cpp_result)


if __name__ == "__main__":
    main()
