import atexit
import json
import multiprocessing
from typing import Optional

import dash
from dash import Input, Output, callback, html

from loomistd.state import StateService
from loomiverse.hfq.specs import proxy_state_spec
from loomix.logging import setup_logging

# Global state service
_state_service: Optional[StateService] = None


def get_state_service():
    """Get state service instance."""
    global _state_service

    if _state_service is None:
        multiprocessing.freeze_support()
        setup_logging(".logs", log_level=20)

        _state_service = StateService(proxy_state_spec)
        _state_service.initialize()

        atexit.register(lambda: _state_service.shutdown() if _state_service else None)

    return _state_service


# Initialize Dash app
app = dash.Dash(__name__)

# Simple layout with refresh button
app.layout = html.Div(
    [
        html.H1("State Viewer"),
        html.Button("Refresh", id="refresh-btn", n_clicks=0),
        html.Div(id="status"),
        html.Pre(
            id="state-display",
            style={
                "backgroundColor": "#f0f0f0",
                "padding": "10px",
                "border": "1px solid #ccc",
                "fontFamily": "monospace",
                "whiteSpace": "pre-wrap",
                "maxHeight": "80vh",
                "overflow": "auto",
            },
        ),
    ]
)


@callback(
    [Output("state-display", "children"), Output("status", "children")],
    Input("refresh-btn", "n_clicks"),
)
def update_display(n_clicks):
    """Update display when refresh button is clicked."""
    print(f"Refresh clicked: {n_clicks}")

    # Get state service
    state_service = get_state_service()

    # Get state
    state = state_service.state

    # Try different ways to access data
    with state.with_dict_view() as view:
        data = view.extract()

    # Format for display
    if data:
        display_text = json.dumps(data, indent=2, default=str)
        status_text = f"✅ Connected - Data retrieved (refresh #{n_clicks})"
    else:
        display_text = "Connected but no data found"
        status_text = f"⚠️ Connected but empty (refresh #{n_clicks})"

    return display_text, status_text


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app.run(debug=False, port=8050)
