import atexit
import json
import multiprocessing
from typing import Optional

import dash
from dash import Input, Output, callback, dcc, html

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

# Layout with auto-refresh
app.layout = html.Div(
    [
        html.H1("State Viewer"),
        dcc.Interval(
            id="interval-component", interval=2000, n_intervals=0  # 0.1 seconds in milliseconds
        ),
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
    Input("interval-component", "n_intervals"),
)
def update_display(n_intervals):
    """Update display automatically every 0.1 seconds."""

    # Get state service
    state_service = get_state_service()

    # Get state
    state = state_service.state

    data = {}

    with state.with_dict_view() as view:
        # Get candles
        with view.at("canldes").with_list_view() as candles:
            lengeth = candles.length()
            if lengeth > 0:
                data["candles"] = [
                    candles.get(canlde_index) for canlde_index in range(lengeth - 10, lengeth)
                ]

        # Get trades
        with view.at("trades").with_list_view() as trades:
            length = trades.length()
            if length > 0:
                data["trades"] = [
                    trades.get(trade_index) for trade_index in range(length - 10, length)
                ]

    # Format for display
    if data:
        display_text = json.dumps(data, indent=2, default=str)
        status_text = f"✅ Connected - Updates: {n_intervals}"
    else:
        display_text = "Connected but no data found"
        status_text = f"⚠️ Connected but empty - Updates: {n_intervals}"

    return display_text, status_text


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app.run(debug=False, port=8050)
