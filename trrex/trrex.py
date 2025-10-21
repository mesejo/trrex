from io import StringIO
from typing import Dict, Sequence, Tuple


_OPTION: Tuple[str, Dict, bool] = ("?", {}, False)
_OPEN_PARENTHESIS: Tuple[str, Dict, bool] = ("(?:", {}, False)
_CLOSE_PARENTHESIS: Tuple[str, Dict, bool] = (")", {}, False)
_OPEN_BRACKETS: Tuple[str, Dict, bool] = ("[", {}, False)
_CLOSE_BRACKETS: Tuple[str, Dict, bool] = ("]", {}, False)
_ALTERNATION: Tuple[str, Dict, bool] = ("|", {}, False)


class _Trie:
    def __init__(self, words, left=r"\b", right=r"\b"):
        self.left = left
        self.right = right
        self.root = ({}, False)
        for word in sorted(words):
            node, is_terminal = self.root
            size = len(word)
            for i, char in enumerate(word):
                is_terminal = i == size - 1
                if char not in node:
                    node[char] = ({}, is_terminal)
                node, is_terminal = node[char]

    def _to_regex(self):
        stack = [(self.left,) + self.root]
        cumulative = StringIO()

        while stack:
            char, children, end = stack.pop()
            cumulative.write(char)

            if not children:
                continue  # skip

            if end:
                stack.append(_OPTION)

            single, multiple = [], []
            for key, (values, terminal) in children.items():
                if values:
                    multiple.append((key, values, terminal))
                else:
                    single.append((key, values, terminal))

            requires_character_set = len(single) > 1
            requires_alternation = (multiple and single) or len(multiple) > 1
            requires_group = requires_alternation or (end and multiple)

            if requires_group:
                stack.append(_CLOSE_PARENTHESIS)

            if requires_character_set:
                stack.append(_CLOSE_BRACKETS)

            for child in single:
                stack.append(child)

            if requires_character_set:
                stack.append(_OPEN_BRACKETS)

            if requires_alternation and single:
                stack.append(_ALTERNATION)

            if multiple:
                head, *tail = multiple
                stack.append(head)

                for child in tail:
                    stack.append(_ALTERNATION)
                    stack.append(child)

            if requires_group:
                stack.append(_OPEN_PARENTHESIS)

        return cumulative.getvalue()

    def make(self):
        return f"{self._to_regex()}{self.right}"


def make(words: Sequence[str]|Sequence[Tuple[str, ...]], prefix: str = r"\b", suffix: str = r"\b"):
    """Create a string that represents a regular expression object from a set of strings

    Parameters
    ----------
    words : Sequence[str]|Sequence[tuple[str, ...]
        Sequence or set of strings to be made into a regex.  Tuples are also
        accepted in order to support escaping of special characters.

    prefix : str, optional
           Left delimiter for pattern

    suffix : str, optional
           Right delimiter for pattern

    Returns
    -------
    : string
            A string representing a regular expression pattern

    Examples
    --------

    >>> import re
    >>> import trrex as tx
    >>> pattern = tx.make(["baby", "bat", "bad"])
    >>> re.findall(pattern, "The baby was scared by the bad bat.")
    ['baby', 'bad', 'bat']
    """

    return _Trie(words, left=prefix, right=suffix).make()
