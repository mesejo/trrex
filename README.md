<div  align="center">
    <a href="https://github.com/mesejo/trex"><img src="https://raw.githubusercontent.com/mesejo/trex/images/trrex_logo.png" width="150" height="150" alt="trrex logo"/></a>
</div>
&nbsp;
<div align="center">
    <a href="https://github.com/mesejo/trex"><img src="https://img.shields.io/github/actions/workflow/status/mesejo/trex/ci-test.yaml" alt="Trrex"></a>
    <a href="https://pepy.tech/project/trrex"><img src="https://pepy.tech/badge/trrex" alt="Downloads"></a>
    <a href="https://pypi.org/project/trrex"><img src="https://img.shields.io/pypi/v/trrex.svg" alt="PyPI Version"></a>
    <a href="https://pypi.org/project/trrex"><img src="https://img.shields.io/pypi/status/trrex.svg" alt="Package Status"></a>
    <a href="https://codecov.io/gh/mesejo/trex"><img src="https://codecov.io/gh/mesejo/trex/branch/master/graph/badge.svg" alt="Code Coverage Status"></a>
     <a href="https://trrex.readthedocs.io"><img src="https://readthedocs.org/projects/trrex/badge/?version=latest" alt="Documentation Status"></a>
</div>

# Efficient string matching with regular expressions

This package includes a pure Python function that enables you to represent a set of strings as a regular expression.
With this regular expression, you can perform various operations, such as replacing, extracting and matching keywords.
The name of the package comes from the internal trie used to build the regular expression (**TR**ie to **RE**ge**X**)

## Install trrex

Use pip,

```bash
pip install trrex
```

## Usage

```python
import trrex as tx
import re

pattern = tx.make(['baby', 'bat', 'bad'])
hits = re.findall(pattern, 'The baby was scared by the bad bat.')
# hits = ['baby', 'bad', 'bat']
```

### pandas

```python
import trrex as tx
import pandas as pd

frame = pd.DataFrame({
    "txt": ["The baby", "The bat"]
})
pattern = tx.make(['baby', 'bat', 'bad'], prefix=r"\b(", suffix=r")\b") # need to specify capturing groups
frame["match"] = frame["txt"].str.extract(pattern)
hits = frame["match"].tolist()
print(hits)
# hits = ['baby', 'bat']
```

## Why use trrex?

- trrex builds a *better* regex pattern, than the simple regex union, therefore searching (and replacing) strings is
about 300 times faster than a regex union pattern, and about 2.5 times faster than FlashText algorithm. See below for a performance
comparison:

![Performance comparison](https://github.com/mesejo/trex/blob/images/find_comparison.png?raw=true)

- Plays well with others, can be integrated easily with pandas, spacy and any other regex engine. See the [documentation](https://trrex.readthedocs.io/en/latest/integration.html)
for examples.
- Pure Python, no other dependencies




## Issues

If you have any issues with this repository, please don't hesitate to [raise them](https://github.com/mesejo/trex/issues/new).
It is actively maintained, and we will do our best to help you.

## Acknowledgments

This project is based on the following resources:

- [Speed up regex](https://stackoverflow.com/questions/42742810/speed-up-millions-of-regex-replacements-in-python-3)
- [Triegex](https://github.com/ZhukovAlexander/triegex)

## Liked the work?
If you've found this repository helpful, why not give it a star? It's an easy way to show your appreciation and support for the project.
Plus, it helps others discover it too!
