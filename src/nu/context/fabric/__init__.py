"""The fabric axis of the Context: lifecycle interactions for provisioning.

- ``Fabric`` - marker protocol for resources that host their own Refs +
  Interactions (Ray cluster, Invisibles transport, Virtuals store, ...).
- ``Resource`` - protocol for anything with a setup / cleanup lifecycle.
- ``Provide`` / ``ProvideList`` / ``ProvideDict`` - Brackets that construct
  a resource on entry, bind it on ctx, and tear down in reverse on exit.

Both sync and async lifecycles are supported through the two open methods on
each bracket - the async runtime prefers ``asetup`` / ``acleanup`` when
defined and falls back to sync ``setup`` / ``cleanup``. The Nu tree is the DI
system: an inner resource reads its deps from ctx during its own setup.
"""

from __future__ import annotations

from .lifecycle import Provide, ProvideDict, ProvideList
from .protocol import Fabric
from .resource import Resource


__all__ = ["Fabric", "Provide", "ProvideDict", "ProvideList", "Resource"]
