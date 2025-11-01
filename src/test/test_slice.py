from inexmo import compile


@compile()
def parse_slice(length: int, s: slice) -> list[int]:  # type: ignore[empty-body]
    """
    py::ssize_t start = 0, stop = 0, step = 0, slice_length = 0;
    if (!s.compute(10, &start, &stop, &step, &slice_length)) {
        throw py::error_already_set();
    }
    std::vector<int> indices;
    indices.reserve(slice_length);
    for (py::ssize_t i = 0; i < slice_length; ++i) {
        indices.push_back(start + i * step);
    }
    return indices;
    """


def test_slice() -> None:
    assert parse_slice(10, slice(1, None, 2)) == [1, 3, 5, 7, 9]
    assert parse_slice(10, slice(None, None, -2)) == [9, 7, 5, 3, 1]
    assert parse_slice(10, slice(5, 1, -1)) == [5, 4, 3, 2]
    assert parse_slice(10, slice(None, 2, -2)) == [9, 7, 5, 3]


if __name__ == "__main__":
    test_slice()
