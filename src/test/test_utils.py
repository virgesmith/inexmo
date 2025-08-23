from inexmo.utils import group_headers


def test_group_headers_basic() -> None:
    headers = [
        "<vector>",
        '"local.h"',
        "<thirdparty.h>",
        "<string>",
        '"code.inl"',
        '"another_local.hpp"',
        "<anotherthirdparty.hpp>",
        "<pybind11/stl.h>",
        "<map>",
    ]
    result = group_headers(headers)
    # Expected order:
    # 1. inlined code
    # 2. "local.h", "another_local.h"
    # 3. <thirdparty.h>, <anotherthirdparty.h>
    # 4. <vector>, <string>, <map>
    expected = [
        ['"code.inl"'],
        ['"local.h"', '"another_local.hpp"'],
        ["<thirdparty.h>", "<anotherthirdparty.hpp>", "<pybind11/stl.h>", "<pybind11/pybind11.h>"],
        ["<vector>", "<string>", "<map>"],
    ]
    assert result == expected


def test_group_headers_only_local() -> None:
    headers = ['"foo.h"', '"bar.h"']
    assert group_headers(headers) == [[], ['"foo.h"', '"bar.h"'], ["<pybind11/pybind11.h>"], []]


def test_group_headers_only_thirdparty() -> None:
    headers = ["<lib.h>", "<otherlib.h>"]
    assert group_headers(headers) == [[], [], ["<lib.h>", "<otherlib.h>", "<pybind11/pybind11.h>"], []]


def test_group_headers_only_stdlib() -> None:
    headers = ["<vector>", "<string>"]
    assert group_headers(headers) == [[], [], ["<pybind11/pybind11.h>"], ["<vector>", "<string>"]]


def test_group_headers_other() -> None:
    headers = ["<vector>", '"custom.inl"']
    assert group_headers(headers) == [['"custom.inl"'], [], ["<pybind11/pybind11.h>"], ["<vector>"]]


def test_group_headers_empty() -> None:
    assert group_headers([]) == [[], [], ["<pybind11/pybind11.h>"], []]


def test_group_headers_mixed_with_spaces() -> None:
    headers = [
        "  <vector>  ",
        ' "local.h" ',
        "<thirdparty.h> ",
        "<string>",
        "other_header ",
    ]
    # Only '<string>' matches stdlib, '<thirdparty.h> ' matches thirdparty, '"local.h" ' matches local, others are "other"
    expected = [["other_header"], ['"local.h"'], ["<thirdparty.h>", "<pybind11/pybind11.h>"], ["<vector>", "<string>"]]
    assert group_headers(headers) == expected
