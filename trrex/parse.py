from sre_constants import (
    ANY,
    AT,
    AT_BEGINNING,
    AT_BEGINNING_STRING,
    AT_BOUNDARY,
    AT_END,
    AT_END_STRING,
    AT_NON_BOUNDARY,
    CATEGORY,
    CATEGORY_DIGIT,
    CATEGORY_NOT_DIGIT,
    CATEGORY_NOT_SPACE,
    CATEGORY_NOT_WORD,
    CATEGORY_SPACE,
    CATEGORY_WORD,
    IN,
    LITERAL,
    MAX_REPEAT,
    MAXREPEAT,
    MIN_REPEAT,
    NEGATE,
    NOT_LITERAL,
    RANGE,
)
from sre_parse import (  # type: ignore
    ASCIILETTERS,
    CATEGORIES,
    DIGITS,
    HEXDIGITS,
    OCTDIGITS,
    REPEAT_CHARS,
    SPECIAL_CHARS,
    State,
    SubPattern,
    Tokenizer,
)

_REPEATCODES = frozenset({MIN_REPEAT, MAX_REPEAT})

ESCAPES = {
    r"\a": (LITERAL, r"\a"),
    r"\b": (LITERAL, r"\b"),
    r"\f": (LITERAL, r"\f"),
    r"\n": (LITERAL, r"\n"),
    r"\r": (LITERAL, r"\r"),
    r"\t": (LITERAL, r"\t"),
    r"\v": (LITERAL, r"\v"),
    r"\\": (LITERAL, r"\\"),
}


def _uniq(items):
    return list(dict.fromkeys(items))


def _escape(source, escape):
    # handle escape code in expression
    code = CATEGORIES.get(escape)
    if code:
        return code
    code = ESCAPES.get(escape)
    if code:
        return code
    try:
        c = escape[1:2]
        if c == "x":
            # hexadecimal escape
            escape += source.getwhile(2, HEXDIGITS)
            if len(escape) != 4:
                raise source.error("incomplete escape %s" % escape, len(escape))
            return LITERAL, int(escape[2:], 16)
        elif c == "u" and source.istext:
            # unicode escape (exactly four digits)
            escape += source.getwhile(4, HEXDIGITS)
            if len(escape) != 6:
                raise source.error("incomplete escape %s" % escape, len(escape))
            return LITERAL, int(escape[2:], 16)
        elif c == "U" and source.istext:
            # unicode escape (exactly eight digits)
            escape += source.getwhile(8, HEXDIGITS)
            if len(escape) != 10:
                raise source.error("incomplete escape %s" % escape, len(escape))
            c = int(escape[2:], 16)
            chr(c)  # raise ValueError for invalid code
            return LITERAL, c
        elif c == "N" and source.istext:
            c = extract_named_unicode(source)
            return LITERAL, c
        elif c == "0":
            # octal escape
            escape += source.getwhile(2, OCTDIGITS)
            return LITERAL, int(escape[1:], 8)
        elif c in DIGITS:
            # octal escape *or* decimal group reference (sigh)
            if source.next in DIGITS:
                escape += source.get()
                if (
                    escape[1] in OCTDIGITS
                    and escape[2] in OCTDIGITS
                    and source.next in OCTDIGITS
                ):
                    # got three octal digits; this is an octal escape
                    escape += source.get()
                    c = int(escape[1:], 8)
                    if c > 0o377:
                        raise source.error(
                            "octal escape value %s outside of "
                            "range 0-0o377" % escape,
                            len(escape),
                        )
                    return LITERAL, c
        if len(escape) == 2:
            if c in ASCIILETTERS:
                raise source.error("bad escape %s" % escape, len(escape))
            return LITERAL, rf"\{escape[1]}"
    except ValueError:
        pass
    raise source.error("bad escape %s" % escape, len(escape))


def extract_named_unicode(source):
    import unicodedata

    # named unicode escape e.g. \N{EM DASH}
    if not source.match("{"):
        raise source.error("missing {")
    charname = source.getuntil("}", "character name")
    try:
        c = ord(unicodedata.lookup(charname))
    except (KeyError, TypeError):
        raise source.error(
            "undefined character name %r" % charname,
            len(charname) + len(r"\N{}"),
        )
    return c


def _class_escape(source, escape):
    # handle escape code inside character class
    code = ESCAPES.get(escape)
    if code:
        return code
    code = CATEGORIES.get(escape)
    if code and code[0] is IN:
        return code
    try:
        c = escape[1:2]
        if c == "x":
            # hexadecimal escape (exactly two digits)
            escape += source.getwhile(2, HEXDIGITS)
            if len(escape) != 4:
                raise source.error("incomplete escape %s" % escape, len(escape))
            return LITERAL, int(escape[2:], 16)
        elif c == "u" and source.istext:
            # unicode escape (exactly four digits)
            escape += source.getwhile(4, HEXDIGITS)
            if len(escape) != 6:
                raise source.error("incomplete escape %s" % escape, len(escape))
            return LITERAL, int(escape[2:], 16)
        elif c == "U" and source.istext:
            # unicode escape (exactly eight digits)
            escape += source.getwhile(8, HEXDIGITS)
            if len(escape) != 10:
                raise source.error("incomplete escape %s" % escape, len(escape))
            c = int(escape[2:], 16)
            chr(c)  # raise ValueError for invalid code
            return LITERAL, c
        elif c == "N" and source.istext:
            c = extract_named_unicode(source)
            return LITERAL, c
        elif c in OCTDIGITS:
            # octal escape (up to three digits)
            escape += source.getwhile(2, OCTDIGITS)
            c = int(escape[1:], 8)
            if c > 0o377:
                raise source.error(
                    "octal escape value %s outside of " "range 0-0o377" % escape,
                    len(escape),
                )
            return LITERAL, c
        elif c in DIGITS:
            raise ValueError
        if len(escape) == 2:
            if c in ASCIILETTERS:
                raise source.error("bad escape %s" % escape, len(escape))
            return LITERAL, ord(escape[1])
    except ValueError:
        pass
    raise source.error("bad escape %s" % escape, len(escape))


def _parse_sub(source, state, nested):
    # parse a simple pattern
    subpattern = SubPattern(state)

    # precompute constants into local variables
    subpatternappend = subpattern.append
    sourceget = source.get
    sourcematch = source.match
    _len = len
    _ord = ord

    while True:
        this = source.next
        if this is None:
            break  # end of pattern
        if this in "|)":
            break  # end of subpattern
        sourceget()

        if this[0] == "\\":
            code = _escape(source, this)
            subpatternappend(code)

        elif this not in SPECIAL_CHARS:
            subpatternappend((LITERAL, _ord(this)))

        elif this == "[":
            here = source.tell() - 1
            # character set
            set = []
            setappend = set.append
            if source.next == "[":
                import warnings

                warnings.warn(
                    "Possible nested set at position %d" % source.tell(),
                    FutureWarning,
                    stacklevel=nested + 6,
                )
            negate = sourcematch("^")
            # check remaining characters
            while True:
                this = sourceget()
                if this is None:
                    raise source.error(
                        "unterminated character set", source.tell() - here
                    )
                if this == "]" and set:
                    break
                elif this[0] == "\\":
                    code1 = _class_escape(source, this)
                else:
                    if set and this in "-&~|" and source.next == this:
                        import warnings

                        warnings.warn(
                            "Possible set %s at position %d"
                            % (
                                "difference"
                                if this == "-"
                                else "intersection"
                                if this == "&"
                                else "symmetric difference"
                                if this == "~"
                                else "union",
                                source.tell() - 1,
                            ),
                            FutureWarning,
                            stacklevel=nested + 6,
                        )
                    code1 = LITERAL, _ord(this)
                if sourcematch("-"):
                    # potential range
                    that = sourceget()
                    if that is None:
                        raise source.error(
                            "unterminated character set", source.tell() - here
                        )
                    if that == "]":
                        if code1[0] is IN:
                            code1 = code1[1][0]
                        setappend(code1)
                        setappend((LITERAL, _ord("-")))
                        break
                    if that[0] == "\\":
                        code2 = _class_escape(source, that)
                    else:
                        if that == "-":
                            import warnings

                            warnings.warn(
                                "Possible set difference at position %d"
                                % (source.tell() - 2),
                                FutureWarning,
                                stacklevel=nested + 6,
                            )
                        code2 = LITERAL, _ord(that)
                    if code1[0] != LITERAL or code2[0] != LITERAL:
                        msg = "bad character range %s-%s" % (this, that)
                        raise source.error(msg, len(this) + 1 + len(that))
                    lo = code1[1]
                    hi = code2[1]
                    if hi < lo:
                        msg = "bad character range %s-%s" % (this, that)
                        raise source.error(msg, len(this) + 1 + len(that))
                    setappend((RANGE, (lo, hi)))
                else:
                    if code1[0] is IN:
                        code1 = code1[1][0]
                    setappend(code1)

            set = _uniq(set)
            # XXX: <fl> should move set optimization to compiler!
            if _len(set) == 1 and set[0][0] is LITERAL:
                # optimization
                if negate:
                    subpatternappend((NOT_LITERAL, set[0][1]))
                else:
                    subpatternappend(set[0])
            else:
                if negate:
                    set.insert(0, (NEGATE, None))
                # charmap optimization can't be added here because
                # global flags still are not known
                subpatternappend((IN, set))

        elif this in REPEAT_CHARS:
            # repeat previous item
            here = source.tell()
            if this == "?":
                min, max = 0, 1
            elif this == "*":
                min, max = 0, MAXREPEAT

            elif this == "+":
                min, max = 1, MAXREPEAT
            elif this == "{":
                if source.next == "}":
                    subpatternappend((LITERAL, _ord(this)))
                    continue

                min, max = 0, MAXREPEAT
                lo = hi = ""
                while source.next in DIGITS:
                    lo += sourceget()
                if sourcematch(","):
                    while source.next in DIGITS:
                        hi += sourceget()
                else:
                    hi = lo
                if not sourcematch("}"):
                    subpatternappend((LITERAL, _ord(this)))
                    source.seek(here)
                    continue

                if lo:
                    min = int(lo)
                    if min >= MAXREPEAT:
                        raise OverflowError("the repetition number is too large")
                if hi:
                    max = int(hi)
                    if max >= MAXREPEAT:
                        raise OverflowError("the repetition number is too large")
                    if max < min:
                        raise source.error(
                            "min repeat greater than max repeat", source.tell() - here
                        )
            else:
                raise AssertionError("unsupported quantifier %r" % (this,))
            # figure out which item to repeat
            if subpattern:
                item = subpattern[-1:]
            else:
                item = None
            if not item or item[0][0] is AT:
                raise source.error(
                    "nothing to repeat", source.tell() - here + len(this)
                )
            if item[0][0] in _REPEATCODES:
                raise source.error("multiple repeat", source.tell() - here + len(this))
            if sourcematch("?"):
                subpattern[-1] = (MIN_REPEAT, (min, max, item))
            else:
                subpattern[-1] = (MAX_REPEAT, (min, max, item))

        elif this == ".":
            subpatternappend((ANY, None))

        elif this == "(":
            raise NotImplementedError("No nested patterns")

        elif this == "^":
            subpatternappend((AT, AT_BEGINNING))

        elif this == "$":
            subpatternappend((AT, AT_END))

        else:
            raise AssertionError("unsupported special character %r" % (this,))

    return subpattern


def parse(string):
    source = Tokenizer(string)
    state = State()
    state.str = string
    items = sub_parse(source, state, 0)

    return _items_to_list_of_nodes(items)


def extract_not_literal_node(val):
    node = extract_literal_node(val)
    return f"[^{node}]"


def extract_min_repeat_node(val):
    start, end, pat = val
    p = ""

    for op, v in pat:
        if op == LITERAL:
            p += extract_literal_node(v)
        elif op == IN:
            p += extract_in_node(v)

    if end == MAXREPEAT:
        if start == 0:
            return f"{p}*?"
        else:
            return f"{p}+?"

    return rf"{p}{{{start},{end}}}?"


def _items_to_list_of_nodes(items):
    patterns = []
    for item in items:
        nodes = []
        for op, val in item:
            if op == IN:
                nodes.append(extract_in_node(val))
            elif op == LITERAL:
                nodes.append(extract_literal_node(val))
            elif op == NOT_LITERAL:
                nodes.append(extract_not_literal_node(val))
            elif op == ANY:
                nodes.append(".")
            elif op == AT:
                nodes.append(extract_at_node(val))
            elif op == MAX_REPEAT:
                nodes.append(extract_max_repeat_node(val))
            elif op == MIN_REPEAT:
                nodes.append(extract_min_repeat_node(val))
        patterns.append(nodes)
    return patterns


def extract_at_node(val):
    if val == AT_BOUNDARY:
        return r"\b"
    elif val == AT_BEGINNING:
        return "^"
    elif val == AT_END:
        return "$"
    elif val == AT_NON_BOUNDARY:
        return r"\B"
    elif val == AT_BEGINNING_STRING:
        return r"\A"
    elif val == AT_END_STRING:
        return r"\Z"


def extract_literal_node(val):
    if isinstance(val, str) and "\\" in val:
        return val
    return chr(val)


def extract_in_node(val):
    ii = ""
    category = False
    for a, v in val:
        if a == CATEGORY:
            if v == CATEGORY_DIGIT:
                ii += r"\d"
            elif v == CATEGORY_NOT_DIGIT:
                ii += r"\D"
            elif v == CATEGORY_SPACE:
                ii += r"\s"
            elif v == CATEGORY_NOT_SPACE:
                ii += r"\S"
            elif v == CATEGORY_WORD:
                ii += r"\w"
            elif v == CATEGORY_NOT_WORD:
                ii += r"\W"
            category = True
        elif a == RANGE:
            start, end = v
            ii += f"{chr(start)}-{chr(end)}"
        elif a == LITERAL:
            ii += extract_literal_node(v)
        elif a == NEGATE:
            ii += "^"
    return ii if category and len(val) == 1 else f"[{ii}]"


def sub_parse(source, state, nested):
    items = []
    items_append = items.append
    source_match = source.match
    while True:
        items_append(_parse_sub(source, state, nested + 1))
        if not source_match("|"):
            break

    return items


def extract_max_repeat_node(val):
    start, end, pat = val
    p = ""

    for op, v in pat:
        if op == LITERAL:
            p += extract_literal_node(v)
        elif op == IN:
            p += extract_in_node(v)

    if end == MAXREPEAT:
        if start == 0:
            return f"{p}*"
        else:
            return f"{p}+"

    return rf"{p}{{{start},{end}}}"
