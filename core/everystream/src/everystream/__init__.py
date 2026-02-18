"""everystream -- Event stream substrate for everybase.

Push-based event processing: pub/sub, webhooks, SSE, WebSockets.
Subscribe, receive, process -- not request-response.

Target systems: Kafka, Redis Pub/Sub, AMQP, NATS, WebSockets, SSE, webhooks.

Architecture::

    everybase (core: Term, Flow, Context, Span)
    +-- everyshape     -- document-model substrate (hierarchical, uniform CRUD)
    +-- everystream    -- event stream substrate (pub/sub, consume)
"""

from __future__ import annotations
