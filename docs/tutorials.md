## Advanced usage

By default, trrex will use word boundaries `"(\\b)"` to delimit keywords,
this could be problematic if the words contain punctuation symbols. You
can do the following for those cases:

```python
import trrex as tx
import re

emoticons = [":)", ":D", ":("]
pattern = tx.make(emoticons,
                  prefix=r"(?<!w)",
                  suffix=r"(?!w)")
result = re.findall(pattern, "The smile :), and the laugh :D and the sad :(")
```

In the above example the parenthesis need no escaping because they are
inside in a character set:

In general, however, the regex meta characters need to be escaped in
order to match them:

```python
words = ["bab.y", "b#ad", "b?at"]
# apply re.escape to each character of each word
pattern = tx.make(tuple(map(re.escape, word)) for word in words)
```

Notice that you need to apply
[re.escape](https://docs.python.org/3/library/re.html#re.escape) to
*each character of each string* in order to work properly with trrex.

## How not to use it

The code below makes a pattern for each word and hence does not take
advantage of trrex. The code will offer no performance benefit against a
standard Python string search.

```python
import trrex as tx
import re

text = "The bad bat scared the baby"
words = ["bad", "baby", "bat"]
for word in words:
    pattern = tx.make([word])
    match = re.search(pattern, text)
```
