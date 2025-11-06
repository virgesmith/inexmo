from xenoform import compile


def test_cxx_std() -> None:
    # TODO why does clang only warn???
    @compile(cxx_std=23, extra_includes=["<memory>"])
    def f(i: int) -> bool:  # type: ignore[empty-body]
        "return *std::auto_ptr<bool>(new bool(i % 2));"

    f(3)


if __name__ == "__main__":
    test_cxx_std()
