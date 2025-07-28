from typing import Annotated

from inexmo import compile


# this isn't actually a template specialisation it uses py::bytes since it won't convert to std::vector<uint8_t>
@compile()
def len_bytes(a: bytes) -> Annotated[int, "std::size_t"]:  # type: ignore[empty-body]
    """
    // clunky...
    py::buffer_info info(py::buffer(a).request());
    return static_cast<std::size_t>(info.size);
    """


def test_bytes() -> None:
    assert len_bytes("9¾".encode()) == 3


if __name__ == "__main__":
    test_bytes()
