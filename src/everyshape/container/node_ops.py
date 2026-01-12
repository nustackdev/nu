"""Node identification and information gathering.

This module provides core node operations for identifying node types and
gathering information about nodes without performing validation.

Hot path optimizations:
- node_exists: Direct storage check without creating NodeInfo
- get_node_type: Quick type check without full info gathering
- get_node_info: Comprehensive info when needed
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from everyshape._types import NOT_SET, NotSet, is_notset
from everyshape.loc import site as site_
from everyshape.types import Empty

from .context import require_read_context
from .marker import extract_marker
from .types import NodeInfo, NodeType, ParentChainInfo, ParentInfo


if TYPE_CHECKING:
    from everyshape.storage import StorageContextType
    from everyshape.types import Value

__all__ = [
    "gather_parent_info",
    "get_node_info",
    "get_node_type",
    "node_exists",
]


def node_exists(site: site_.Site, ctx: StorageContextType) -> bool:
    """Check if node exists at site.

    Optimized hot path - performs minimal work to determine existence.

    Args:
        site: Site to check
        ctx: Storage context (transaction, snapshot or write batch)

    Returns:
        True if node exists, False otherwise
    """
    return require_read_context(ctx).exists(site)


def get_node_type(
    site: site_.Site, ctx: StorageContextType, *, raw_value: Value | Empty | NotSet = NOT_SET
) -> NodeType:
    """Get node type without full information gathering.

    Optimized for hot path - determines type without creating full NodeInfo.

    Args:
        site: Site to check
        ctx: Storage context (transaction, snapshot or write batch)
        raw_value: Prefetched value to parse info from

    Returns:
        NodeType: CONTAINER, PRIMITIVE, or NOT_FOUND
    """
    if is_notset(raw_value):
        raw_value = require_read_context(ctx).get(site)
        if isinstance(raw_value, Empty):
            return NodeType.NOT_FOUND
        return NodeType.CONTAINER if extract_marker(raw_value) else NodeType.PRIMITIVE
    elif isinstance(raw_value, Empty):
        return NodeType.NOT_FOUND
    else:
        return (
            NodeType.CONTAINER if extract_marker(cast("Value", raw_value)) else NodeType.PRIMITIVE
        )


def get_node_info(
    site: site_.Site, ctx: StorageContextType, *, raw_value: Value | Empty | NotSet = NOT_SET
) -> NodeInfo:
    """Get complete node information.

    Gathers all available information about a node including type-specific
    attributes. This is the comprehensive version used when full data is needed.

    Args:
        site: Site to gather information about
        ctx: Storage context (transaction, snapshot or write batch)
        raw_value: Prefetched value to parse info from

    Returns:
        NodeInfo with all available data:
        - For containers: site, exists=True, node_type=CONTAINER, structure, protocol
        - For primitives: site, exists=True, node_type=PRIMITIVE, primitive_value
        - For missing: site, exists=False, node_type=NOT_FOUND
    """
    if is_notset(raw_value):
        raw_value = require_read_context(ctx).get(site)

    # Site doesn't exist
    if isinstance(raw_value, Empty):
        return NodeInfo(
            site=site,
            exists=False,
            node_type=NodeType.NOT_FOUND,
        )

    raw_value = cast("Value", raw_value)

    # Try to parse as container marker
    marker_info = extract_marker(raw_value)
    if marker_info is not None:
        structure, protocol = marker_info
        return NodeInfo(
            site=site,
            exists=True,
            node_type=NodeType.CONTAINER,
            raw_value=raw_value,
            structure=structure,
            protocol=protocol,
        )

    # It's a primitive value
    return NodeInfo(
        site=site,
        exists=True,
        node_type=NodeType.PRIMITIVE,
        raw_value=raw_value,
        primitive_value=raw_value,
    )


def gather_parent_info(site: site_.Site, ctx: StorageContextType) -> ParentChainInfo:
    """Gather parent chain information without validation.

    Pure information collection - traverses the site hierarchy from root to
    immediate parent, collecting raw storage data and categorizing sites based
    on existence and data format. Does not make validation decisions.

    Args:
        site: Site to gather parent information for
        ctx: Storage context (transaction, snapshot or write batch)

    Returns:
        ParentChainInfo with raw data about parent chain:
        - chain: All parent infos from root to immediate parent
        - missing_sites: Sites that don't exist in storage
        - malformed_sites: Sites with corrupted markers
    """
    ancestors = site_.get_ancestors(site)
    if not ancestors:
        # Root level - no parents
        return ParentChainInfo(
            chain=(),
            missing_sites=(),
            malformed_sites=(),
        )

    parent_infos = []
    missing_sites = []
    malformed_sites = []

    for ancestor_site in ancestors:
        info = get_node_info(ancestor_site, ctx)

        if not info.exists:
            parent_info = ParentInfo(
                site=ancestor_site,
                exists=False,
            )
            parent_infos.append(parent_info)
            missing_sites.append(ancestor_site)

        elif info.node_type == NodeType.CONTAINER:
            # Check if marker is well-formed
            if info.structure is None or info.protocol is None:
                parent_info = ParentInfo(
                    site=ancestor_site,
                    exists=True,
                    structure=None,
                    protocol=None,
                    raw_type_data=None,  # Malformed
                )
                parent_infos.append(parent_info)
                malformed_sites.append(ancestor_site)
            else:
                parent_info = ParentInfo(
                    site=ancestor_site,
                    exists=True,
                    structure=info.structure,
                    protocol=info.protocol,
                    raw_type_data=None,
                )
                parent_infos.append(parent_info)

        else:
            # Primitive at parent location - malformed
            parent_info = ParentInfo(
                site=ancestor_site,
                exists=True,
                structure=None,
                protocol=None,
                raw_type_data=info.primitive_value,
            )
            parent_infos.append(parent_info)
            malformed_sites.append(ancestor_site)

    return ParentChainInfo(
        chain=tuple(parent_infos),
        missing_sites=tuple(missing_sites),
        malformed_sites=tuple(malformed_sites),
    )
