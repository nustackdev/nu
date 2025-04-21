"""
Streamlit Dashboard Runner for Loomi Workflow Visualization.

This module provides functions for running the Streamlit dashboard
to visualize Loomi workflow execution.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from loomistd.kv_storage.file_storage import FileStorageSpec
from loomistd.state import StateSpec
from loomix.ui.dashboard.render import apply_custom_css, render_dashboard, setup_streamlit_page
from loomix.ui.service import VisualizationService, VisualizationServiceSpec


async def initialize_session_state():
    """Initialize Streamlit session state."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
        st.session_state.last_update = time.time()
        st.session_state.selected_operation = None
        st.session_state.last_refresh = datetime.now()
        st.session_state.tracing_data = {
            "operations": {},
            "execution": {},
            "graph": {},
            "metadata": {},
        }
        st.session_state.execution_timeline = []


async def run_dashboard(
    spec: VisualizationServiceSpec,
    page_title: str = "Loomi Workflow Dashboard",
    page_icon: str = "🔄",
    page_layout: str = "wide",
):
    """
    Run the Streamlit dashboard.

    Args:
        tracing_path: Path in state where tracing data is stored
        state_spec: Optional state specification
        page_title: Title for the Streamlit page
        page_icon: Icon for the Streamlit page
        page_layout: Layout for the Streamlit page
    """
    # Setup Streamlit page
    setup_streamlit_page(page_title, page_icon, page_layout)

    # Initialize session state
    await initialize_session_state()

    vis_service = VisualizationService(spec)
    if not vis_service._is_initialized:
        await vis_service.initialize()

    try:
        # Apply custom CSS from theme
        apply_custom_css(vis_service.theme.ui_styles.get("css", ""))

        # Load tracing data
        tracing_data = await vis_service.load_tracing_data()
        st.session_state.tracing_data = tracing_data
        st.session_state.last_refresh = vis_service.get_last_refresh()

        # Render dashboard
        render_dashboard(tracing_data, vis_service.get_renderer(), st.session_state.last_refresh)
    finally:
        # Shut down visualization service
        await vis_service.shutdown()


if __name__ == "__main__":
    tracing_state_spec = StateSpec(
        name="tracing_state", storage_srv=FileStorageSpec(path=Path(".tracing/db"))
    )
    spec = VisualizationServiceSpec(state=tracing_state_spec)
    asyncio.run(run_dashboard(spec))
