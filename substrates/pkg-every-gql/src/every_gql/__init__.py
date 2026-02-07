"""every_gql -- GraphQL substrate for everybase.

Schema-driven graph traversal. Client-defined response shapes.
Query construction as the morphism.

Target APIs: GitHub GraphQL, Shopify, Hasura, AppSync.

Architecture:

    everybase (core: Term, Flow, Context, Span)
    +-- everyshape     -- document-model substrate (hierarchical, uniform CRUD)
    +-- everyservice   -- service substrate (flat, unique methods)
    +-- everyrest      -- REST/HTTP substrate (hierarchical, CRUD + unique actions)
    +-- everystream    -- event stream substrate (pub/sub, consume)
    +-- every-gql      -- GraphQL substrate (schema graph, client-defined queries)
"""

from __future__ import annotations
