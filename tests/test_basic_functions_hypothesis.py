import re
from string import ascii_letters, punctuation

from hypothesis import example, given
from hypothesis.strategies import lists, text

from trrex import make


def compile(lst, flags=0, left=r"\b", right=r"\b"):
    return re.compile(make(lst, left, right), flags)


@given(text(alphabet=ascii_letters, min_size=1))
def test_single_string_match(s):
    pattern = compile([s])
    assert pattern.match(s) is not None


@example(lst=["B", "BA", "B"])
@given(lists(text(alphabet=ascii_letters, min_size=1)))
def test_multiple_string_match(lst):
    pattern = compile(lst)
    for word in lst:
        assert pattern.match(word) is not None


@given(lists(text(alphabet=ascii_letters + punctuation, min_size=1)))
def test_multiple_string_match_punctuation(lst):
    words = [tuple(map(re.escape, word)) for word in lst]
    pattern = compile(words, left="", right="")
    for word in lst:
        assert pattern.match(word) is not None
