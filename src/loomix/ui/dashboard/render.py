"""
Streamlit visualization components.

This module provides utility functions for rendering workflow visualization
components in Streamlit.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, cast

import pandas as pd
import streamlit as st

from loomix.ui.dashboard.graph import GraphRenderer


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to a readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 0.001:
        return "<1ms"
    elif seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"


def render_status_badge(status: str) -> str:
    """
    Render a status badge with appropriate styling.

    Args:
        status: Status string (pending, running, completed, error)

    Returns:
        HTML for the status badge
    """
    status_icons = {"pending": "⏳", "running": "🔄", "completed": "✅", "error": "❌"}

    icon = status_icons.get(status, "⚪")

    return (
        f'<span class="status-badge status-{status}">'
        f'<span class="status-icon">{icon}</span>{status.capitalize()}'
        f"</span>"
    )


def get_operation_status_count(tracing_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Get counts of operations by status.

    Args:
        tracing_data: Dictionary containing tracing data

    Returns:
        Dictionary with operation counts by status
    """
    operations = tracing_data.get("operations", {})
    execution = tracing_data.get("execution", {})
    graph = tracing_data.get("graph", {})

    total = len(graph)
    running = len(execution)
    completed = sum(1 for op in operations.values() if op.get("status") == "completed")
    error = sum(1 for op in operations.values() if op.get("status") == "error")
    pending = total - running - completed - error

    return {
        "total": total,
        "pending": pending,
        "running": running,
        "completed": completed,
        "error": error,
    }


def update_execution_timeline(tracing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Update the execution timeline with recent events.

    Args:
        tracing_data: Dictionary containing tracing data

    Returns:
        List of timeline events sorted by time
    """
    # Combine operations and current execution
    all_ops = {}
    for op_id, op_data in tracing_data.get("operations", {}).items():
        all_ops[op_id] = op_data

    for op_id, op_data in tracing_data.get("execution", {}).items():
        if op_id not in all_ops:
            all_ops[op_id] = op_data

    # Create timeline entries
    timeline = []
    for op_id, op_data in all_ops.items():
        # Get operation name
        op_name = op_data.get("op_name", "Unknown")
        op_type = op_data.get("op_type", "Operation")

        # Get custom display name if available
        metadata = tracing_data.get("metadata", {}).get(op_id, {})
        display_name = metadata.get("display_name", op_name)

        # Add start event if available
        if "start_time" in op_data:
            timeline.append(
                {
                    "time": op_data["start_time"],
                    "event": "start",
                    "op_id": op_id,
                    "op_name": display_name,
                    "op_type": op_type,
                    "status": "running",
                }
            )

        # Add end event if available
        if "end_time" in op_data:
            timeline.append(
                {
                    "time": op_data["end_time"],
                    "event": "end",
                    "op_id": op_id,
                    "op_name": display_name,
                    "op_type": op_type,
                    "status": op_data.get("status", "completed"),
                }
            )

    # Sort by time
    timeline.sort(key=lambda x: x["time"])

    return timeline


def render_operation_details(op_id: str, tracing_data: Dict[str, Any]) -> None:
    """
    Render detailed information about a selected operation.

    Args:
        op_id: ID of the operation to display
        tracing_data: Dictionary containing tracing data
    """
    if not op_id:
        st.info("Select an operation to view details")
        return

    # Get operation data
    graph_data = tracing_data.get("graph", {}).get(op_id, {})
    op_data = tracing_data.get("operations", {}).get(op_id, {})
    exec_data = tracing_data.get("execution", {}).get(op_id, {})
    meta_data = tracing_data.get("metadata", {}).get(op_id, {})

    # Combine data (execution data takes precedence over operation data)
    data = {**op_data} if op_data else {**exec_data} if exec_data else {}

    # Get operation name and type
    op_name = data.get("op_name", "Unknown")
    op_type = data.get("op_type", "Operation")

    # Get custom display name if available
    display_name = meta_data.get("display_name", op_name)

    # Determine status
    status = "pending"
    if op_id in tracing_data.get("execution", {}):
        status = "running"
    elif op_id in tracing_data.get("operations", {}):
        status = tracing_data["operations"][op_id].get("status", "pending")

    # Display operation info
    st.markdown(f"### {display_name}")
    st.markdown(f"**Type:** {op_type}")

    # Display status with styling
    st.markdown(f"**Status:** {render_status_badge(status)}", unsafe_allow_html=True)

    # Display timing information
    if "start_time" in data:
        start_time = datetime.fromtimestamp(data["start_time"]).strftime("%H:%M:%S.%f")[:-3]
        st.markdown(f"**Started:** {start_time}")

    if "end_time" in data:
        end_time = datetime.fromtimestamp(data["end_time"]).strftime("%H:%M:%S.%f")[:-3]
        st.markdown(f"**Ended:** {end_time}")

    if "duration" in data:
        st.markdown(f"**Duration:** {format_duration(data['duration'])}")
    elif "start_time" in data and status == "running":
        # Calculate elapsed time for running operations
        elapsed = time.time() - data["start_time"]
        st.markdown(f"**Running for:** {format_duration(elapsed)}")

    # Display error if present
    if "error" in data:
        st.error(f"**Error:** {data['error']}")

    # Display description if available
    if "description" in meta_data and meta_data["description"]:
        st.markdown("**Description:**")
        st.markdown(meta_data["description"])

    # Display relationships
    col1, col2 = st.columns(2)

    # Parent relationship
    parent_id = graph_data.get("parent")
    if parent_id:
        parent_data = tracing_data.get("graph", {}).get(parent_id, {})
        parent_meta = tracing_data.get("metadata", {}).get(parent_id, {})
        parent_name = parent_meta.get("display_name", parent_data.get("name", parent_id))

        with col1:
            st.markdown("**Parent:**")
            if st.button(f"Go to {parent_name}", key=f"goto_parent_{parent_id}"):
                st.session_state.selected_operation = parent_id
                st.rerun()

    # Children relationships
    children = graph_data.get("children", [])
    if children:
        with col2:
            st.markdown("**Children:**")
            for i, child_id in enumerate(children):
                child_data = tracing_data.get("graph", {}).get(child_id, {})
                child_meta = tracing_data.get("metadata", {}).get(child_id, {})
                child_name = child_meta.get("display_name", child_data.get("name", child_id))

                if st.button(f"Go to {child_name}", key=f"goto_child_{child_id}_{i}"):
                    st.session_state.selected_operation = child_id
                    st.rerun()

    # Display context attributes if present
    if "context_attrs" in data and data["context_attrs"]:
        st.markdown("**Context Attributes:**")
        st.json(data["context_attrs"])

    # Display custom properties if present
    if "custom_properties" in meta_data and meta_data["custom_properties"]:
        st.markdown("**Custom Properties:**")
        st.json(meta_data["custom_properties"])


def render_timeline(timeline: List[Dict[str, Any]]) -> None:
    """
    Render execution timeline.

    Args:
        timeline: List of timeline events
    """
    if not timeline:
        st.info("No execution events recorded yet")
        return

    # Create a DataFrame for the timeline
    df = pd.DataFrame(timeline)
    df["formatted_time"] = df["time"].apply(
        lambda x: datetime.fromtimestamp(x).strftime("%H:%M:%S.%f")[:-3]
    )

    # Sort by time (most recent first)
    df = df.sort_values("time", ascending=False)

    # Take only the most recent events (up to 10)
    df = df.head(10)

    # Display the timeline
    for _, event in df.iterrows():
        # Create a formatted event message
        if event["event"] == "start":
            message = f"Started {event['op_name']} ({event['op_type']})"
            icon = "🔄"
        else:  # end event
            status = event["status"]
            if status == "completed":
                message = f"Completed {event['op_name']} ({event['op_type']})"
                icon = "✅"
            elif status == "error":
                message = f"Error in {event['op_name']} ({event['op_type']})"
                icon = "❌"
            else:
                message = f"Ended {event['op_name']} ({event['op_type']}) with status {status}"
                icon = "⚪"

        # Clickable event that sets the selected operation
        if st.button(
            f"{icon} {message} ({event['formatted_time']})",
            key=f"timeline_{event['op_id']}_{event['time']}",
            use_container_width=True,
        ):
            st.session_state.selected_operation = event["op_id"]
            st.rerun()


def render_dashboard(
    tracing_data: Dict[str, Any], renderer: GraphRenderer, last_refresh: datetime
) -> None:
    """
    Render the main dashboard.

    Args:
        tracing_data: Dictionary containing tracing data
        renderer: GraphRenderer instance to use for rendering
        last_refresh: Timestamp of the last data refresh
    """
    # Header section
    st.title("🔄 Loomi Workflow Dashboard")

    # Display last refresh time
    refresh_time = last_refresh.strftime("%H:%M:%S")
    st.caption(f"Last refreshed: {refresh_time}")

    # Main layout with columns
    left_col, right_col = st.columns([3, 1])

    with left_col:
        # Graph visualization
        st.subheader("Workflow Graph")

        # Render graph if data is available
        if tracing_data.get("graph", {}):
            # Render graph
            graph = renderer.render_graph(
                tracing_data["graph"],
                tracing_data.get("operations", {}),
                tracing_data.get("execution", {}),
                tracing_data.get("metadata", {}),
                st.session_state.get("selected_operation"),
            )

            # Display the graph
            st.graphviz_chart(graph, use_container_width=True)
        else:
            st.info("No workflow data available. Waiting for execution to start...")

    with right_col:
        # Status counter cards
        st.subheader("Execution Status")
        status_counts = get_operation_status_count(tracing_data)

        # Overall progress
        if status_counts["total"] > 0:
            progress = status_counts["completed"] / status_counts["total"]
            st.progress(progress)

        # Status cards in a grid
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total", status_counts["total"])
            st.metric("Running", status_counts["running"], delta=None)

        with col2:
            st.metric("Completed", status_counts["completed"], delta=None)
            st.metric("Errors", status_counts["error"], delta=None)

        # Add manual refresh button
        if st.button("🔄 Refresh Now", type="primary", use_container_width=True):
            st.rerun()

        # Operation selection
        st.subheader("Select Operation")

        # Create a dictionary of operation names by ID
        operation_names = {}
        for op_id, op_info in tracing_data.get("graph", {}).items():
            # Try to get display name from metadata
            meta = tracing_data.get("metadata", {}).get(op_id, {})
            display_name = meta.get("display_name", op_info.get("name", op_id))
            operation_names[op_id] = display_name

        # Sort operations by name
        sorted_ops = sorted(operation_names.items(), key=lambda x: x[1])

        # Create selectbox options
        options = ["None"] + [op_id for op_id, _ in sorted_ops]
        option_format = {op_id: name for op_id, name in sorted_ops}
        option_format["None"] = "Select an operation..."

        # Display selectbox
        selected = st.selectbox(
            "Select operation to view details",
            options,
            format_func=lambda x: option_format.get(x, x),
            index=(
                0
                if st.session_state.get("selected_operation") is None
                else (
                    options.index(st.session_state["selected_operation"])
                    if st.session_state.get("selected_operation") in options
                    else 0
                )
            ),
        )

        if selected != "None" and selected != st.session_state.get("selected_operation"):
            st.session_state.selected_operation = selected
            st.rerun()

    # Operation details section
    st.markdown("---")

    # Use columns for operation details and timeline
    detail_col, timeline_col = st.columns([2, 1])

    with detail_col:
        st.subheader("Operation Details")
        render_operation_details(
            cast(str, st.session_state.get("selected_operation")),
            tracing_data,
        )

    with timeline_col:
        st.subheader("Recent Events")
        timeline = update_execution_timeline(tracing_data)
        render_timeline(timeline)


def apply_custom_css(css: str) -> None:
    """
    Apply custom CSS to the Streamlit app.

    Args:
        css: CSS string to apply
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def setup_streamlit_page(title: str, icon: str, layout: str = "wide") -> None:
    """
    Set up the Streamlit page configuration.

    Args:
        title: Page title
        icon: Page icon
        layout: Page layout
    """
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,  # type: ignore
        initial_sidebar_state="expanded",
    )
