# Substrate Taxonomy — Integration Paradigms

How different distributed system paradigms map to everybase substrates.

The substrate distinction is by **modeling topology** — how resources are addressed and what operations exist — not by transport (HTTP vs gRPC vs local).


## The Axis

```
                    Uniform ops                   Unique ops per entity
                    (CRUD / get-set-delete)        (unique methods, queries, actions)
                    ─────────────────────          ──────────────────────────────────
Hierarchical        everyshape                     ???
(nested, path-      (dict, PV, doc stores)
 based addressing)

Flat / identity     eb_rest (CRUD + actions)     eb_service (RPC)
(entity + id)       (Stripe, GitHub, Notion)       (Solana, gRPC, SOAP)
```


## 1. GraphQL APIs

**Examples**: GitHub GraphQL, Shopify, Hasura, AppSync

**Topology**: Client-defined graph traversal. Server exposes schema, client queries subgraphs. Response shape is determined by query, not server.

**Key traits**:
- Schema-driven (introspectable)
- Client specifies exactly what fields to return
- Nested queries in a single request
- Mutations for writes (named, unique — not CRUD verbs)

**Substrate**: `eb-gql` (future). Different paradigm from both everyshape (client defines shape) and eb_service (graph traversal, not flat methods). Query construction is the morphism.


## 2. REST / HTTP APIs (the real-world middle ground)

**Examples**: GitHub REST, Stripe, Twilio, Notion, Slack, most SaaS

**Topology**: Resources with identity, HTTP verbs for CRUD, plus unique actions. Usually 1-3 levels of resource nesting. The 90% of "REST APIs" that aren't Fielding-grade.

**Key traits**:
- Resources identified by URL templates (`/repos/{owner}/{name}`)
- Standard CRUD via HTTP verbs (GET/POST/PUT/PATCH/DELETE)
- Unique actions that break CRUD (`PUT /pulls/{n}/merge`, `POST /messages/{id}/star`)
- HTTP concerns: auth, pagination, rate limiting, headers, caching
- Mix of uniform and unique ops — typically ~50-80% CRUD, rest unique

**Substrate**: `eb_rest`. Auto-derived CRUD from resource model + explicit unique actions. HTTP-aware adapter layer.


## 3. Event Streams / Hooks

**Examples**: Kafka, WebSockets, SSE (Server-Sent Events), webhooks, Redis Pub/Sub, AMQP, NATS, AWS SQS/SNS

**Topology**: Push-based. Events flow from producers to consumers. Not request-response.

**Key traits**:
- Pub/sub or point-to-point
- Ordering guarantees (or lack thereof)
- Backpressure, acknowledgment, replay
- Often append-only (log-like)
- Webhooks: HTTP callback — server pushes to client URL

**Substrate**: `everystream` (or similar). Fundamentally different from request-response substrates. The morphism isn't "call and get result" — it's "subscribe, receive, process." Possible Term model: stream sources, filters, transformations as a term tree. Connects to eb_flow naturally (flows ARE event processing).


## 4. Relational (SQL)

**Examples**: PostgreSQL, MySQL, SQLite, Notion databases, Airtable

**Topology**: Tables, rows, columns. Joins across tables. Query language (SQL or query builders).

**Key traits**:
- Schema-defined tables with typed columns
- Row identity (primary key)
- Relationships via foreign keys
- Query language for filtering, joining, aggregating
- Transactions, ACID guarantees
- Notion DBs / Airtable: simplified relational with API access

**Substrate**: `everytable` (already exists in workspace). Tables + rows + queries. The morphism is query construction (SELECT/INSERT/UPDATE/DELETE with WHERE clauses, joins). Different from both everyshape (no joins, no query language) and eb_service (structured queries, not arbitrary methods).


## 5. Service / RPC (flat methods)

**Examples**: Solana JSON-RPC, Ethereum JSON-RPC, gRPC services, SOAP, Twirp, tRPC

**Topology**: Flat method dispatch. No resource hierarchy. Each method has unique signature and semantics.

**Key traits**:
- Method name + arguments → result
- No resource model (or very thin)
- Often schema-defined (protobuf for gRPC, WSDL for SOAP, OpenRPC for JSON-RPC)
- Stateless per-call
- May be sync or async (streaming RPCs)

**Substrate**: `eb_service` (current). Interface + ServiceMethodCall. Flat identity, unique methods.


## 6. Other Paradigms

### Document Stores (MongoDB, CouchDB, Firestore)
Hierarchical, uniform-ish CRUD. Closest to everyshape — nested documents with get/set/delete. Could be an everyshape adapter (thick-ish for HTTP/network, but same topology).

### Key-Value Stores (Redis, DynamoDB, etcd, Memcached)
Flat KV with get/set/delete. Subset of everyshape (single-level, no nesting). PV already covers this.

### File / Object Storage (S3, GCS, local filesystem)
Hierarchical (bucket/prefix/key or directory/file), uniform ops (read/write/delete/list). Very close to everyshape. Could be an everyshape adapter with streaming for large objects.

### Search Engines (Elasticsearch, Algolia, MeiliSearch)
Query-driven. You index documents (everyshape-like) and search with complex queries (closer to relational/GQL). Hybrid — indexing is CRUD, searching is query construction.

### Time Series (InfluxDB, Prometheus, TimescaleDB)
Append-heavy, query by time range + tags. Specialized relational. Could be everytable with time-aware query morphisms.

### Graph Databases (Neo4j, ArangoDB, Amazon Neptune)
Native graph traversal. Nodes + edges + properties. Close to GQL paradigm. Could share substrate with eb-gql or be its own thing.


## Summary Table

| Paradigm | Addressing | Ops | Substrate | Status |
|---|---|---|---|---|
| Document stores | hierarchical paths | uniform CRUD | everyshape | exists |
| Key-value stores | flat keys | uniform CRUD | everyshape (PV) | exists |
| File/object storage | hierarchical paths | uniform CRUD + streams | everyshape adapter | future |
| Relational/SQL | tables + rows + queries | CRUD + query language | everytable | exists |
| REST/HTTP APIs | URL templates + identity | CRUD + unique actions | eb_rest | **new** |
| RPC/flat services | flat methods | unique per method | eb_service | exists |
| Event streams | topics/channels | pub/sub/consume | everystream | **new** |
| GraphQL | schema graph | client-defined queries | eb-gql | future |
| Search engines | index + query | CRUD + search queries | hybrid | future |
| Time series | time + tags | append + range query | everytable variant | future |
| Graph databases | nodes + edges | traversal + CRUD | eb-gql variant | future |
