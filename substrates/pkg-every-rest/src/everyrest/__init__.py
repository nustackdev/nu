"""everyrest -- REST/HTTP API substrate for everybase.

Resources with auto-derived CRUD + explicit unique actions.
HTTP-aware adapter layer (URL templates, auth, pagination).

Target APIs: GitHub, Stripe, Twilio, Notion, Slack, and most SaaS REST APIs.

Architecture::

    everybase (core: Term, Flow, Context, Span)
    +-- everyshape     -- document-model substrate (hierarchical, uniform CRUD)
    +-- everyservice   -- service substrate (flat, unique methods)
    +-- everyrest      -- REST/HTTP substrate (hierarchical, CRUD + unique actions)
"""

from __future__ import annotations
