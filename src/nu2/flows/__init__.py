"""Generic reactive control flows for Nu2.

Flows consume change subscriptions from the shape fabric and execute bodies
in response. They are not shape-specific — any Nu2 program composing reactive
event handling uses these atoms.

- ``React``        - wait for one change event, execute body once.
- ``ReactWhile``   - execute body on each change while condition is truthy.
- ``ReactForever`` - execute body on every change; runs forever.
- ``Stream``       - drain-then-follow over an ordered collection.
"""

from .react import React, ReactForever, ReactWhile
from .stream import Stream


__all__ = ["React", "ReactForever", "ReactWhile", "Stream"]
