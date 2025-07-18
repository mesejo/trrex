import re

from trrex import make


def compile(lst, flags=0, left=r"\b", right=r"\b"):
    return re.compile(make(lst, left, right), flags)


def test_findall():
    words = ["baby", "bad", "bat"]
    pattern = compile(words)
    assert pattern.findall("The baby was bitten by the bad bat") == words


def test_findall_ignore_case():
    words = ["baby", "bad", "bat"]
    pattern = compile(words, flags=re.IGNORECASE)
    actual = pattern.findall("The BABY was bitten by the bAD Bat")
    assert words == [w.lower() for w in actual]


def test_findall_whitespace():
    words = ["Ray Steam"]
    pattern = compile(words)
    actual = pattern.findall("Ray Steam is Steamboy")
    assert words == actual


def test_match():
    name = "Ray Steam"
    pattern = compile([name, "Edward Elric"])
    match = pattern.match(name)
    assert match is not None


def test_sub():
    replacements = {"Ray Steam": "Steamboy"}
    pattern = compile(list(replacements.keys()))

    def replace(match):
        return replacements.get(match.group(), "")

    actual = pattern.sub(replace, "The kid Ray Steam save the day")
    assert "The kid Steamboy save the day" == actual


def test_findall_punctuation():
    words = ["bab.y", "b#ad", "b?at"]
    pattern = compile(tuple(map(re.escape, word)) for word in words)
    assert pattern.findall("The bab.y was bitten by the b#ad b?at") == words


def test_match_punctuation():
    word = ":"
    pattern = compile([word], left="", right="")
    match = pattern.match(word)
    assert match is not None


def test_findall_emoticon():
    emoticons = [":)", ":D", ":("]
    pattern = compile(emoticons, left=r"(?<!\w)", right=r"(?!\w)")
    assert pattern.findall("The smile :), and the laugh :D and the sad :(") == emoticons
