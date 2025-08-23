# Inline Extension Modules

Write and execute superfast C or C++ inside your Python code! Here's how...

Write a function or method definition **in python**, add the `compile` decorator and put the C++ implementation in a
docstr:

```py
import inexmo

@inexmo.compile()
def max(i: int, j: int) -> int:  # type: ignore[empty-body]
  "return i > j ? i : j;"
```

When Python loads this file, the source for an extension module is generated with all functions using this decorator.
The first time any function is called, the module is built and the attribute corresponding to the (empty) Python
function is replaced with the C++ implementation in the module.

Modules are only rebuilt when changes to the any of the functions in the module (or decorator parameters)
are detected.

The binaries, source code and build logs for the compiled modules can be found in the `ext` folder.

## Features

- Supports [`numpy` arrays](https://pybind11.readthedocs.io/en/stable/advanced/pycpp/numpy.html) for customised
"vectorised" operations. You can either implement the function directly, or write a scalar function and make
use of pybind11's auto-vectorisation feature, if appropriate. (Parallel library support out of the
box may vary, e.g. on a mac, you may need to manually `brew install libomp` for openmp support)
- Supports positional and keyword arguments with defaults, including positional-only and keyword-only markers (`/`,`*`), `*args`
and `**kwargs`
- Using annotated types, you can:
    - qualify C++ arguments by value, reference, or (dumb) pointer, with or without `const`
    - override the default mapping of python types to C++ types
- Automatically includes (minimal) required headers for compilation
- Compound types are supported, by mapping (by default) to `std::optional` / `std::variant`
- Custom macros and extra headers/compiler/linker commands can be added as necessary
- Can link to separate C++ sources, prebuilt libraries, see [test_external_source.py](src/test/test_external_source.py) [test_external_static.py](src/test/test_external_static.py) and
[test_external_shared.py](src/test/test_external_shared.py) for details.

Caveats & points to note:

- Compiled python lambdas are not supported but nested functions are, in a limited way - they cannot capture variables from
their enclosing scope
- Top-level recursion is not supported, since the functions themselves are implemented as anonymous C++ lambdas. For a
workaround see the Fibonacci example in [test_types.py](src/test/test_types.py)
- Functions with conflicting headers or compiler/linker settings must be implemented in separate modules
- Auto-vectorisation naively applies operations to
[vector inputs in a piecewise manner](https://pybind11.readthedocs.io/en/stable/advanced/pycpp/numpy.html#vectorizing-functions),
and although it will broadcast lower-dimensional arguments where possible (e.g. adding a scalar to a vector), it is
not suitable for more complex operations (e.g. matrix multiplication)
- Using auto-vectorisation incurs a major performance penalty when the function is called with all scalar arguments
- Header files are ordered in sensible groups (inline code, local headers, library headers, system headers) but there
is currently no way to fine-tune this ordering
- For methods, type annotations must be provided for the context: `self: Self` for instance methods, or `cls: type` for class methods.
- IDE syntax highlighting and linting probably won't work correctly for inline C or C++ code. A workaround is to have
the inline code just call a function in a separate `.cpp` file.
- Any changes to `#include`-d files won't automatically trigger a rebuild - the module will need to be
manually deleted

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
`pd.Series` and `pd.DataFrame` are implemented in terms of numpy arrays, I this example we use the python object API
to construct and extract the underlying arrays, taking advantage of the shallow-copy semantics. A C++ type override
(`py::object`) is required as there is no direct C++ equivalent of `pd.Series`, so we need to explicitly add pybind11's
numpy header:

```py
from typing import Annotated

from inexmo import compile

@compile(extra_headers=["<pybind11/numpy.h>"])
def calc_balances_cpp(data: Annotated[pd.Series, "py::object"], rate: float) -> Annotated[pd.Series, "py::object"]:  # type: ignore[empty-body]
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

Full code is in [examples/loop.py](./examples/loop.py). To run the example scripts, install the "examples" extra, e.g.
`pip install inexmo[examples]` or `uv sync --extra examples`.

### `numpy` and vectorised operations

> "vectorisation" in this sense means implementing loops in compiled, rather than interpreted, code. In fact, the C++ implementation below also uses optimisations including "true" vectorisation (meaning hardware SIMD instructions).

For "standard" linear algebra and array operations, implementations in *inexmo* are very unlikely to improve on heavily
optimised numpy implementations such as matrix multiplication.

However, significant performance improvements may be seen for more "bespoke" operations, particularly for
larger objects (the pybind11 machinery has a constant overhead).
p
For example, to compute a distance matrix between $N$ points in $D$ dimensions, an efficient `numpy` implementation
could be:

```py
def calc_dist_matrix_py(p: npt.NDArray) -> npt.NDArray:
    "Compute distance matrix from points, using numpy"
    return np.sqrt(((p[:, np.newaxis, :] - p[np.newaxis, :, :]) ** 2).sum(axis=2))
```
bearing in mind there is some redundancy here as the resulting matrix is symmetric; however vectorisation with
redundancy will always win the tradeoff against loops with no redundancy.

In C++ this tradeoff does not exist. A reasonably well optimised C++ implementation using *inexmo* is:

```py
from inexmo import compile

@compile(extra_compile_args=["-fopenmp"], extra_link_args=["-fopenmp"])
def calc_dist_matrix_cpp(points: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:  # type: ignore[empty-body]
    """
```
```cpp
    py::buffer_info buf = points.request();
    if (buf.ndim != 2)
        throw std::runtime_error("Input array must be 2D");

    size_t n = buf.shape[0];
    size_t d = buf.shape[1];

    py::array_t<double> result({n, n});
    auto r = result.mutable_unchecked<2>();
    auto p = points.unchecked<2>();

    // Avoid redundant computation for symmetric matrix
    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < n; ++i) {
        r(i, i) = 0.0;
        for (size_t j = i + 1; j < n; ++j) {
            double sum = 0.0;
            #pragma omp simd reduction(+:sum)
            for (size_t k = 0; k < d; ++k) {
                double diff = p(i, k) - p(j, k);
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

N | py (ms) | cpp (ms) | speedup (%)
-:|--------:|---------:|-----------:
100 | 0.5 | 2.5 | -82%
300 | 3.2 | 2.2 | 46%
1000 | 43.3 | 13.6 | 218%
3000 | 208.2 | 82.5 | 152%
10000 | 2269.0 | 803.2 | 183%

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
`Self` | `py::object`
`type` | `py::type`
`*args` | `py::args`
`**kwargs` | `const py::kwargs&`

Thus, `dict[str, list[float]]` becomes - by default -  `std::unordered_map<std::string, std::vector<double>>`

### Qualifiers

In Python function arguments are always passed by "value reference" (essentially a modifiable reference to an immutable* object), but C++ is more flexible. The default mapping uses by-value, which when objects are shallow-copied, (like numpy arrays) is often sufficient. To change this behaviour, annotate the function arguments, passing an appropriate instance of `CppQualifier`, e.g.:

&ast; unless its a `dict`, `list`, `set` or `bytearray`

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
`RRef` | `T&&`
`Ptr` | `T*`
`PtrC` | `T* const`
`CPtr` | `const T*`
`CPtrC` | `const T* const`

(NB pybind11 does not appear to support `std::shared_ptr` or `std::unique_ptr` as function arguments)


### Overriding

In some circumstances, you may want to provide a custom mapping. This is done by passing the required C++ type (as a string) in the annotation. For example, to restrict interger inputs and outputs to nonnegative values, use an unsigned type:

```py
from typing import Annotated

from inexmo import compile

@compile()
def fibonacci(n: Annotated[int, "uint64_t"]) -> Annotated[int, "uint64_t"]:
    ...
```

Other use cases for overriding:
- for types that are not known to pybind11 or C++ but you want to make the function's intent clear: e.g.
`Annotated[pd.Series, "py::object"]` (rather than the uninformative `Any`)
- for compound (optional and union) types when you want to access them as a generic python object
rather than via the default mapping - which uses the `std::optional` and `std::variant` templates.

## Troubleshooting

The generated module source code is written to `module.cpp`. Compiler output is redirected to `build.log` in the same
folder. NB build logs are not produced when running via pytest, due to they way it captures output streams.

## TODO

- [X] default arguments, kwargs and pos-only/kw-only args?
- [X] `*args` and `**kwargs`
- [ ] return value policy
- [ ] customisable location of modules (default seems to work ok)?
- [ ] better control over header file order?
- [ ] are modules consistently rebuilding/reloading (only) when signature/code/compiler setting change?
- [X] function docstr (supplied as help arg to compile)
- [ ] come up with a better name!


## See also

[https://pybind11.readthedocs.io/en/stable/](https://pybind11.readthedocs.io/en/stable/)
