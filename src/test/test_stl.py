from inexmo import compile


@compile(extra_headers=["<numeric>"])
def vector_sum(v: list[int]) -> int:  # type: ignore[empty-body]
    """
    return std::accumulate(v.begin(), v.end(), 0);
    """


def test_vector() -> None:
    assert vector_sum([1, 2, 3, 4]) == 10
    assert vector_sum(range(5)) == 10


@compile(extra_headers=["<numeric>"])
def set_sum(s: set[int]) -> int:  # type: ignore[empty-body]
    """
    return std::accumulate(s.begin(), s.end(), 0);
    """


def test_set() -> None:
    assert set_sum({1, 2, 3, 4}) == 10


@compile(extra_headers=["<numeric>"])
def map_sum(d: dict[int, int]) -> int:  # type: ignore[empty-body]
    """
    return std::accumulate(d.begin(), d.end(), 0, [](int value, std::pair<int,int> p) { return value + p.second; });
    """


def test_map() -> None:
    assert map_sum({i: i + 1 for i in range(4)}) == 10


@compile()
def tuple_sum(t4: tuple[int, int, int, int]) -> int:  # type: ignore[empty-body]
    """
    // summing a C++ tuple is not straightforward
    return std::get<0>(t4) + std::get<1>(t4) + std::get<2>(t4) + std::get<3>(t4);
    """


def test_tuple() -> None:
    assert tuple_sum([1, 2, 3, 4]) == 10
    assert tuple_sum(range(4)) == 6


if __name__ == "__main__":
    test_vector()
