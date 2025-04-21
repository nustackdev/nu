"""
Visualization Themes.

This module defines theme classes for styling visualizations, including
graph rendering styles and UI components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Theme:
    """
    Theme configuration for visualizations.

    Defines styling for nodes, edges, and other UI elements.

    Attributes:
        node_styles: Styles for different node states
        edge_styles: Styles for different edge states
        graph_attrs: Attributes for the overall graph
        timing_format: Format string for timing labels
        ui_styles: Custom styling for the UI
    """

    node_styles: dict[str, dict[str, str]] = field(default_factory=dict)
    edge_styles: dict[str, dict[str, str]] = field(default_factory=dict)
    graph_attrs: dict[str, str] = field(default_factory=dict)
    timing_format: str = "{:.2f}s"
    ui_styles: dict[str, Any] = field(default_factory=dict)


def DefaultTheme() -> Theme:
    """
    Create the default theme for visualizations.

    Returns:
        A Theme instance with default styling
    """
    return Theme(
        node_styles={
            "pending": {"fillcolor": "lightgray", "style": "filled", "shape": "box"},
            "running": {"fillcolor": "lightblue", "style": "filled,bold", "shape": "box"},
            "completed": {"fillcolor": "lightgreen", "style": "filled", "shape": "box"},
            "error": {"fillcolor": "tomato", "style": "filled", "shape": "box"},
            "paused": {"fillcolor": "yellow", "style": "filled", "shape": "box"},
        },
        edge_styles={
            "pending": {"color": "gray", "penwidth": "1.0"},
            "active": {"color": "blue", "penwidth": "2.5"},
            "completed": {"color": "green", "penwidth": "1.5"},
            "error": {"color": "red", "penwidth": "2.0"},
        },
        graph_attrs={
            "rankdir": "LR",  # Left to right layout
            "bgcolor": "transparent",
            "splines": "ortho",  # Orthogonal edges (straight lines)
            "nodesep": "0.5",  # Space between nodes
            "ranksep": "0.5",  # Space between ranks
        },
        timing_format="{:.2f}s",
        ui_styles={
            "css": """
                .main .block-container {
                    padding-top: 2rem;
                    padding-bottom: 2rem;
                }
                .status-badge {
                    display: inline-block;
                    padding: 0.25rem 0.5rem;
                    border-radius: 0.5rem;
                    font-weight: 500;
                    text-align: center;
                }
                .status-pending {
                    background-color: #f0f0f0;
                    color: #666;
                }
                .status-running {
                    background-color: #b3e0ff;
                    color: #0366d6;
                }
                .status-completed {
                    background-color: #c2e0c6;
                    color: #22863a;
                }
                .status-error {
                    background-color: #ffebe9;
                    color: #d73a49;
                }
                .card {
                    background-color: #f8f9fa;
                    border-radius: 0.5rem;
                    padding: 1rem;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    margin-bottom: 1rem;
                }
                .info-label {
                    font-weight: 500;
                    color: #666;
                }
                .info-value {
                    font-weight: 600;
                }
                .header-icon {
                    font-size: 1.5rem;
                    margin-right: 0.5rem;
                }
                .operation-list {
                    max-height: 200px;
                    overflow-y: auto;
                    border: 1px solid #eee;
                    border-radius: 0.25rem;
                    padding: 0.5rem;
                }
                .timestamp {
                    color: #666;
                    font-size: 0.8rem;
                }
                .refresh-button {
                    font-weight: 500;
                }
                .status-icon {
                    margin-right: 0.25rem;
                }
            """
        },
    )
