import importlib
import inspect
import os
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from functools import cache, lru_cache, wraps
from pathlib import Path
from typing import Any, Callable

import numpy as np
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

from inexmo.cppmodule import FunctionSpec, ModuleSpec
from inexmo.errors import CompilationError
from inexmo.logger import get_logger
from inexmo.utils import _deduplicate, get_function_scope, translate_function_signature

# TODO make this configurable?
module_root_dir = Path("./ext")
# ensure the module directory is available to Python
sys.path.append(str(module_root_dir))

logger = get_logger()

_module_registry: dict[str, ModuleSpec] = defaultdict(ModuleSpec)


def _parse_macros(macro_list: list[str]) -> dict[str, str | None]:
    """Map ["DEF1", "DEF2=3"] to {"DEF1": None, "DEF2": "3"}"""
    return {kv[0]: kv[1] if len(kv) == 2 else None for d in macro_list for kv in [d.split("=", 1)]}


def _build_module_impl(
    module_name: str,
    module_spec: ModuleSpec,
) -> None:
    ext_name = module_name + "_ext"

    module_dir = module_root_dir / ext_name
    module_dir.mkdir(exist_ok=True, parents=True)

    code, hashval = module_spec.make_source(module_name)

    # if a built module already exists, and matches the hash of the source code, just use it
    module = None
    try:
        module = importlib.import_module(f"{ext_name}.{module_name}")
        logger(f"module {ext_name}.{module_name} already exists")
        # TODO verbose mode
        # print(f"Code: {hashval} existing {module.__checksum__}")
        if module.__checksum__ == hashval:
            logger(f"module is up-to-date ({hashval})")
            return
    except ImportError:
        logger(f"module {ext_name}.{module_name} not found")
    else:
        logger(f"module is outdated ({hashval})")

    logger(f"(re)building module {ext_name}.{module_name}")

    # save the code with the hash embedded
    with open(module_dir / "module.cpp", "w") as fd:
        fd.write(code.replace("__HASH__", str(hashval)))

    logger(f"wrote {module_dir}/module.cpp")

    ext_modules = [
        Pybind11Extension(
            module_name,
            ["module.cpp"],
            define_macros=list(_parse_macros(_deduplicate(module_spec.define_macros)).items()),
            extra_compile_args=_deduplicate(module_spec.extra_compile_args),
            extra_link_args=_deduplicate(module_spec.extra_link_args),
            include_dirs=[np.get_include(), *_deduplicate(module_spec.include_paths)],
            cxx_std=module_spec.cxx_std,
        )
    ]

    logger(f"building {ext_name}/{module_name}...")
    cwd = Path.cwd()
    try:
        os.chdir(module_dir)
        # Redirect stdout to a log file (does not work in pytest)
        # Redirecting stderr doesnt work at all
        with open("build.log", "w") as fd:
            with redirect_stdout(fd):  # , redirect_stderr(fd):
                setup(
                    name=ext_name,
                    ext_modules=ext_modules,
                    script_args=["build_ext", "--inplace"],
                    cmdclass={"build_ext": build_ext},
                )
    except SystemExit as e:
        raise CompilationError(str(e) + f". See {cwd}/build.log for more info") from e
    finally:
        os.chdir(cwd)

    logger(f"built {ext_name}/{module_name}")
    if module:
        # logger(f"reloading {ext_name}/{module_name}")
        # importlib.reload(module)
        raise ImportError(f"Loaded module {ext_name}/{module_name} is outdated, please restart the process")


@cache  # unlimited module cache
def _get_module(module_name: str) -> object:
    _build_module_impl(module_name, _module_registry[module_name])
    logger(f"importing compiled module {module_name}")
    return importlib.import_module(f"{module_name}_ext.{module_name}")


@lru_cache  # limited function cache
def _get_function(module_name: str, function_name: str) -> Any:
    module = _get_module(module_name)
    logger(f"retrieved compiled function {module_name}.{function_name}")
    return getattr(module, function_name)


def compile(
    *,
    vectorise: bool = False,
    define_macros: list[str] | None = None,
    extra_includes: list[str] | None = None,
    extra_include_paths: list[str] | None = None,
    extra_compile_args: list[str] | None = None,
    extra_link_args: list[str] | None = None,
    cxx_std: int = 20,
    help: str | None = None,
    verbose: bool = False,
) -> Callable[..., Callable[..., Any]]:
    """
    Decorator factory for compiling C/C++ function implementations into extension modules.

    Parameters:
        vectorise (bool, optional): If True, vectorizes the compiled function for array operations.
        define_macros: list[str] | None = None,
        extra_includes (list[str], optional): Additional header/inline files to include during compilation.
        extra_include_paths (list[str], optional): Additional paths search for headers.
        extra_compile_args (list[str], optional): Extra arguments to pass to the compiler.
        extra_link_args (list[str], optional): Extra arguments to pass to the linker.
        cxx_std (int, optional, default 20): C++ standard to compile
        help (str, optional): Docstring for the function
        verbose (bool, optional, default False): enable debug logging

    Returns:
        Callable[..., Callable[..., Any]]: A function that when called, will return the compiled function.
    """

    if verbose:
        logger.enable()
    else:
        logger.disable()

    def register_function(func: Callable[..., Any]) -> Callable[..., Any]:
        """This registers the function, actual compilation is deferred"""
        scope = get_function_scope(func)

        sig, args, headers = translate_function_signature(func)
        module_name = f"{Path(inspect.getfile(func)).stem}"  # noqa: F821
        function_body = sig + " {" + (func.__doc__ or "") + "}"

        logger(f"registering {module_name}.{func.__name__}")

        if vectorise:
            function_body = f"py::vectorize({function_body})"
            headers.append("<pybind11/numpy.h>")

        arg_defs = "".join(f", {kwarg}" for kwarg in args)

        # need to directly alter the original function's help...
        # for reasons unknown, copying the pybind11 function's docstr to the python stub on first use
        # (in _get_function) doesn't actually work
        if help:
            func.__doc__ = help

        # ...as well as adding the help to the ext module
        function_spec = FunctionSpec(
            name=func.__name__, body=function_body, arg_annotations=arg_defs, scope=scope, help=help
        )

        _module_registry[module_name].add_function(
            function_spec,
            headers=headers + (extra_includes or []),
            include_paths=extra_include_paths or [],
            define_macros=define_macros or [],
            extra_compile_args=extra_compile_args or [],
            extra_link_args=extra_link_args or [],
            cxx_std=cxx_std,
        )

        @wraps(func)
        def call_function(*args: Any, **kwargs: Any) -> Any:
            """Compilation is deferred until here (and cached)"""
            return _get_function(module_name, function_spec.qualified_cpp_name())(*args, **kwargs)

        return call_function

    return register_function
