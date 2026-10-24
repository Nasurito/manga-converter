import argparse

import pytest

from main import parse_chapter_range


@pytest.mark.parametrize("text, expected", [
    ("5", (5, 5)),
    ("1-10", (1, 10)),
    ("10-1", (1, 10)),
    ("12.5", (12.5, 12.5)),
    ("270-271.5", (270, 271.5)),
])
def test_parse_chapter_range(text, expected):
    assert parse_chapter_range(text) == expected


@pytest.mark.parametrize("text", ["abc", "1-", "1-2-3", ""])
def test_parse_chapter_range_invalid(text):
    with pytest.raises(argparse.ArgumentTypeError):
        parse_chapter_range(text)
