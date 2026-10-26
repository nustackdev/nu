"""Container Shape -- the page frame, declared.

A Section over ``ContainerRef``: the size, the gap and the gutter come from
the Ref, and ``slot(**props)`` hands them over as they are.

    class Home(Container):
        heading = HeadingRef.slot(label="Home")
        chart = LineChart.slot()

    home = Home.slot(size="dashboard")
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.collections.container import ContainerRef


__all__ = ["Container"]


class Container(Section):
    """The page frame around its slots. Props as ``ContainerRef.slot``."""

    _ref_cls = ContainerRef
