from time import process_time
from typing import Any

import numpy as np
import pandas as pd

from inexmo import compile

rng = np.random.default_rng(19937)

rate = 0.001


@compile(extra_headers=["<pybind11/numpy.h>"])
def calc_balances_cpp(data: Any, rate: float) -> Any:  # type: ignore[type-var]
    """
    auto pd = py::module::import("pandas");
    auto result = pd.attr("Series")(py::arg("index") = data.attr("index"));

    auto data_a = data.attr("to_numpy")().cast<py::array_t<int64_t>>();
    auto result_a = result.attr("to_numpy")().cast<py::array_t<double>>();

    auto n = data_a.request().shape[0];
    auto d = data_a.unchecked<1>();
    auto r = result_a.mutable_unchecked<1>();

    double current_value = 0.0;
    for (py::ssize_t i = 0; i < n; ++i) {
        current_value = (current_value + d(i)) * (1.0 - rate);
        r(i) = current_value;
    }
    return result;
    """


def calc_balances_py(data: pd.Series, rate: float) -> pd.Series:
    """Cannot vectorise, since each value is dependent on the previous value"""
    result = pd.Series(index=data.index)
    result_a = result.to_numpy()
    current_value = 0.0
    for i, value in data.items():
        current_value = (current_value + value) * (1 - rate)
        result_a[i] = current_value
    return result


def main() -> None:
    """Run a performance comparison for varying series lengths"""
    print("N | py (ms) | cpp (ms) | speedup (%)")
    print("-:|--------:|---------:|-----------:")
    for N in [1000, 10000, 100000, 1000000, 10000000]:
        data = pd.Series(index=range(N), data=rng.integers(-100, 101, size=N), name="cashflow")

        start = process_time()
        py_result = calc_balances_py(data, rate)
        py_time = process_time() - start

        start = process_time()
        # Although we can actually construct a pd.Series in C++, it is simpler to create it in python
        # and pass it to be interpreted as a numpy array. For fairness, this allocation is included in the C++ time
        # cpp_result = pd.Series(index=data.index)
        # calc_balances_cpp(data, rate, cpp_result)
        cpp_result = calc_balances_cpp(data, rate)
        cpp_time = process_time() - start

        print(f"{N} | {py_time * 1000:.1f} | {cpp_time * 1000:.1f} | {100 * (py_time / cpp_time - 1.0):.0f}")
        assert py_result.equals(cpp_result)


if __name__ == "__main__":
    main()
