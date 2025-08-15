# Inline Extension Modules

Write and execute superfast C or C++ inside your Python code! Here's how...

Write a function definition **in python**, add the `compile` decorator and put the C++ implementation in a docstr:

```py
import inexmo

@inexmo.compile()
def max(i: int, j: int) -> int:  # type: ignore[empty-body]
  "return i > j ? i : j;"
```

When Python loads this file, the source for an extension module is generated, including all functions defined in this
way. The first time the function is called, the module is built and the attribute corresponding to the (empty) Python
function is replaced with the C++ implementation in the module.

Modules are only rebuilt when changes to the any of the functions in the module (or decorator parameters)
are detected.

## Features

- Supports [`numpy` arrays](https://pybind11.readthedocs.io/en/stable/advanced/pycpp/numpy.html) for customised
"vectorised" operations. You can either implement the vector function directly, or write a scalar function and make
use of pybind11's auto-vectorisation feature, if appropriate. (Parallel library support out of the
box may vary, e.g. on a mac, you may need to manually `brew install libomp` for openmp support)
- Supports arguments by value, reference, and (dumb) pointer, with or without `const` qualifiers
- Minimal includes by default for performance reasons, can add extra headers as necessary
- Custom compiler and linker commands can be added

Caveats & points to note:

- Compiled functions cannot be nested, they must be defined at file scope
- Functions with conflicting headers or compiler/linker settings must be implemented in separate files
- Using auto-vectorisation incurs a major performance penalty if the function is called with scalar arguments
- Auto-vectorisation naively applies operations to
[vector inputs sequentially](https://pybind11.readthedocs.io/en/stable/advanced/pycpp/numpy.html#vectorizing-functions).
It is not suitable for more complex operations (e.g. matrix multiplication)
- There is currently no way to change the order header files are included in the module source code
- IDE syntax highlighting and linting probably won't work correctly for inline C or C++ code.

## Performance

### Loops

Implementing loops in optimised compiled code can be orders of magnitude faster than loops in Python. Consider this
example: we have a series of cashflows and we need to compute a running balance. The complication is that a fee is
applied to the balance at each step, making each successive value dependent on the previous one, which prevents any
use of vectorisation. The fastest approach in python seems to be preallocating an empty series and accessing it via
numpy:

```py
def calc_balances_py(data: pd.Series, rate: float) -> pd.Series:
    """Cannot vectorise, since each value is dependent on the previous value"""
    result = pd.Series(index=data.index)
    result_a = result.to_numpy()
    current_value = 0.0
    for i, value in data.items():
        current_value = (current_value + value) * (1 - rate)
        result_a[i] = current_value
    return result
```

In C++ we can take essentially the same approach. Although there is no direct C++ API for pandas types, since
`pd.Series` and `pd.DataFrame` are implemented in terms of numpy arrays, we can use the python API to construct
and extract the underlying arrays, taking advantage of the shallow-copy semantics. Series are passed as `Any`
(translates to `py::object`) and so we need to explicitly add pybind11's numpy header:

```py
from inexmo import compile

@compile(extra_headers=["<pybind11/numpy.h>"])
def calc_balances_cpp(data: Any, rate: float) -> Any:
    """
```
```cpp
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
```
```py
    """
```

Needless to say, the C++ implementation vastly outperforms the python (3.13) implementation for all but the smallest arrays:

N | py (ms) | cpp (ms) | speedup (%)
-:|--------:|---------:|-----------:
1000 | 0.7 | 1.1 | -43
10000 | 3.3 | 0.3 | 1067
100000 | 35.1 | 1.7 | 1950
1000000 | 311.5 | 6.5 | 4709
10000000 | 2872.4 | 42.9 | 6601

NB C++ timings include the allocation (in python) of the result.

Full code is in [examples/loop.py](./examples/loop.py). To run the example scripts, install the "examples" extra, e.g.
`pip install inexmo[examples]`.

### `numpy` and vectorised operations

> "vectorisation" in this sense means implementing loops in compiled, rather than interpreted, code. In fact, the C++ implementation below also uses optimisations including "true" vectorisation (meaning hardware SIMD instructions).

For "standard" linear algebra and array operations, implementations in inexmo are very unlikely to improve on heavily
optimised numpy implementations such as matrix multiplication.

However, significant performance improvements may be seen for more "bespoke" operations, particularly for
larger objects (the pybind11 machinery has a constant overhead).

For example, to compute a distance matrix between $N$ points in $D$ dimensions, an efficient `numpy` implementation
could be:

```py
def calc_dist_matrix_p(p: npt.NDArray) -> npt.NDArray:
    "Compute distance matrix from points, using numpy"
    return np.sqrt(((p[:, np.newaxis, :] - p[np.newaxis, :, :]) ** 2).sum(axis=2))
```
bearing in mind there is some redundancy here as the resulting maxtrix is symmetric; however vectorisation with
redundancy will always win the tradeoff against loops with no redundancy.

In C++ this tradeoff does not exist. A reasonably well optimised C++ implementation using `inexmo` is:

```py
from inexmo import compile

@compile(extra_compile_args=["-fopenmp"], extra_link_args=["-fopenmp"])
def calc_dist_matrix_c(p: np_array_t[float]) -> np_array_t[float]:  # type: ignore[empty-body]
    """
```
```cpp
    // compute distance matrix using optimised loops
    py::buffer_info buf = p.request();
    if (buf.ndim != 2)
        throw std::runtime_error("Input array must be 2D");

    size_t n = buf.shape[0];
    size_t d = buf.shape[1];
    auto ptr = static_cast<double *>(buf.ptr);

    py::array_t<double> result({n, n});
    auto r = result.mutable_unchecked<2>();

    // Avoid redundant computation for symmetric matrix
    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < n; ++i) {
        r(i, i) = 0.0;
        for (size_t j = i + 1; j < n; ++j) {
            double sum = 0.0;
            #pragma omp simd reduction(+:sum)
            for (size_t k = 0; k < d; ++k) {
                double diff = ptr[i * d + k] - ptr[j * d + k];
                sum += diff * diff;
            }
            double dist = std::sqrt(sum);
            r(i, j) = dist;
            r(j, i) = dist;
        }
    }
    return result;
```
```py
    """
```

Execution times (in ms) are shown below for each implementation for a varying number of 3d points. Even at relatively small sizes, the compiled implementation is significantly faster.

size | Python | compiled | speedup
----:|-------:|---------:|-------:
100  |    0.5 |      2.4 | -80%
300  |    3.2 |      1.4 | 123%
1000 |   28.8 |     10.4 | 176%
3000 |  201.2 |     68.5 | 194%
10000| 2197.8 |    804.1 | 173%

Full code is in [examples/distance_matrix.py](./examples/distance_matrix.py).

## Type Translations

### Default mapping

Basic Python types are recursively mapped to C++ types, like so:

Python | C++
-------|----
`None` | `void`
`int` | `int`
`np.int32` | `int32_t`
`np.int64` | `int64_t`
`bool` | `bool`
`float` | `double`
`np.float32` | `float`
`np.float64` | `double`
`str` | `std::string`
`np.ndarray` | `py::array_t`
`list` | `std::vector`
`set` | `std::unordered_set`
`dict` | `std::unordered_map`
`tuple` | `std::tuple`
`Any` | `py::object`

Thus, `dict[str, list[float]]` becomes `std::unordered_map<std::string, std::vector<double>>`

### Qualifiers

In Python function arguments are always passed by "value reference", but C++ allows multiple methods. The default mapping uses by-value, which when objects are shallow-copied, (like numpy arrays) is not unreasonable. To change this behaviour, annotate the function arguments, passing an appropriate instance of `CppQualifier`, e.g.:

```py
from typing import Annotated

import numpy as np
import numpy.typing as npt

from inexmo import compile, CppQualifier

@compile()
def do_something(array: Annotated[npt.NDArray[np.float64], CppQualifier.CRef]) -> int:
    ...
```

which will use `const py::array_t<double>&` as the argument type.

Available qualifiers are:

Qualifier | C++
----------|----
`Auto` | `T` (no modification)
`Ref` | `T&`
`CRef` | `const T&`
`RRref` | `T&&`
`Ptr` | `T*`
`PtrC` | `T* const`
`CPtr` | `const T*`
`CPtrC` | `const T* const`

(NB pybind11 does not appear to support `std::shared_ptr` or `std::unique_ptr` as function arguments)


### Overriding

In some circumstances, you may want to provide a custom mapping. This is done by passing the required C++ type (as a string) in the annotation:

```py
from typing import Annotated

from inexmo import compile

@compile()
def do_something(array: Annotated[list[float], "py::list"]) -> int:
    ...
```


## TODO

- [ ] customisable location of modules (default seems to work ok)?
- [ ] control over header file order
- [ ] module builds sometimes need 2 runs to trigger


## See also

[https://pybind11.readthedocs.io/en/stable/](https://pybind11.readthedocs.io/en/stable/)
