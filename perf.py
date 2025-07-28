import time

import numpy as np
import numpy.typing as npt

from inexmo import Platform, compile, platform_specific

# clang doesnt appear to support -fopenmp without installing deps (libomp)
opt_args: dict[Platform, list[str]] = {
    "Linux": ["-fopenmp"],
    "Windows": ["-fopenmp"],
}


@compile(extra_compile_args=platform_specific(opt_args))
def array_max(a: npt.NDArray[float], b: npt.NDArray[float]) -> npt.NDArray[float]:  # type: ignore[empty-body, type-var]
    """
    py::array_t<double> result(std::vector<py::ssize_t>(a.shape(), a.shape() + a.ndim()));

    // this assumes contiguous storage
    const double* pa = static_cast<const double*>(a.request().ptr);
    const double* pb = static_cast<const double*>(b.request().ptr);
    double* r = static_cast<double*>(result.request().ptr);

    #ifndef __APPLE__
    #pragma omp simd
    #endif
    for (py::ssize_t i = 0; i < a.size(); ++i)
    {
      r[i] = pa[i] > pb[i] ? pa[i] : pb[i];
    }
    return result;
    """


@compile(vectorise=True, extra_compile_args=platform_specific(opt_args))
def array_max_autovec(a: float, b: float) -> float:  # type: ignore[empty-body]
    """
    return a > b ? a : b;
    """


def perf_op() -> None:
    ""
    for n in range(1, 5):
        size = 20 * 1024**2 * n
        a = np.random.uniform(size=size)
        b = np.ones(size)

        start = time.process_time()
        cm = array_max(a, b)
        elapsed = time.process_time() - start

        start = time.process_time()
        ca = array_max_autovec(a, b)
        elapsed_autovec = time.process_time() - start

        start = time.process_time()
        # cp = np.where(a > b,  a,  b)
        cp = np.maximum(a, b)
        elapsed_ref = time.process_time() - start

        print(
            f"{8 * size / 1024**3:.1f}GB/array",
            elapsed,
            elapsed_autovec,
            elapsed_ref,
            f"speedup(manual)={elapsed_ref / elapsed - 1:.0%}",
            f"speedup(auto)={elapsed_ref / elapsed_autovec - 1:.0%}",
        )

        assert (cm == cp).all()
        assert (ca == cp).all()


if __name__ == "__main__":
    perf_op()
