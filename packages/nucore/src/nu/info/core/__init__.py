"""Everything that is not specific to a kind.

Knowledge about any Nu thing comes from exactly two places, the code and the
docstring, and there is no third. That split is the layout:

- ``docstring`` reads what was written.
- ``source`` reads what the code says.
- ``contract`` says which written facts are required, merges the two sources
  where a question needs both, and checks the result.

``docstring`` and ``source`` know nothing of Nu or of the contract.
``contract`` knows the contract and nothing of Nu. The kinds sit on top.
"""

from __future__ import annotations


__all__: list[str] = []
