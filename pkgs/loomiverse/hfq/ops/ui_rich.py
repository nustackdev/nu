import atexit
import datetime
import multiprocessing
from typing import Optional

import dash
import pandas as pd
import plotly.graph_objs as go
from dash import Input, Output, dash_table, dcc, html
from loomiverse.hfq.specs import read_only_state_spec

from loomistd.state import StateService
from loomix.logging import setup_logging

# Global state service
_state_service: Optional[StateService] = None


def get_state_service():
    """Get state service instance."""
    global _state_service
    if _state_service is None:
        multiprocessing.freeze_support()
        setup_logging(".logs", log_level=20)
        _state_service = StateService(read_only_state_spec)
        _state_service.initialize()
        atexit.register(lambda: _state_service.shutdown() if _state_service else None)
    return _state_service


# Create fresh Dash app instance
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Custom CSS styling
external_stylesheets = []
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body { margin: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
            .metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important; }
            .status-pulse { animation: pulse 2s infinite; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


def format_timestamp(timestamp):
    """Format timestamp to readable string."""
    return datetime.datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")


def create_stat_card(title, value, subtitle="", color="#3b82f6", icon="📊", trend=None):
    """Create a professional statistics card."""
    trend_indicator = ""
    if trend is not None:
        if trend > 0:
            trend_indicator = html.Span(
                f"↗ +{trend:.1f}%",
                style={"color": "#10b981", "fontSize": "0.85rem", "fontWeight": "600"},
            )
        elif trend < 0:
            trend_indicator = html.Span(
                f"↘ {trend:.1f}%",
                style={"color": "#ef4444", "fontSize": "0.85rem", "fontWeight": "600"},
            )
        else:
            trend_indicator = html.Span(
                "→ 0.0%", style={"color": "#6b7280", "fontSize": "0.85rem", "fontWeight": "600"}
            )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                icon,
                                style={
                                    "fontSize": "2.2rem",
                                    "marginBottom": "12px",
                                    "display": "block",
                                },
                            ),
                            html.Div(
                                str(value),
                                style={
                                    "fontSize": "2.4rem",
                                    "fontWeight": "700",
                                    "color": color,
                                    "lineHeight": "1",
                                    "marginBottom": "8px",
                                },
                            ),
                            html.Div(
                                title,
                                style={
                                    "fontSize": "1rem",
                                    "fontWeight": "600",
                                    "color": "#374151",
                                    "marginBottom": "4px",
                                },
                            ),
                            html.Div(
                                subtitle,
                                style={
                                    "fontSize": "0.875rem",
                                    "color": "#6b7280",
                                    "marginBottom": "8px",
                                },
                            ),
                            trend_indicator,
                        ],
                        style={"textAlign": "center"},
                    )
                ]
            )
        ],
        className="metric-card",
        style={
            "backgroundColor": "white",
            "padding": "24px 20px",
            "borderRadius": "16px",
            "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.05)",
            "border": f"2px solid {color}20",
            "width": "200px",
            "margin": "0 12px",
            "display": "inline-block",
            "transition": "all 0.3s ease",
            "cursor": "default",
        },
    )


# Dashboard Layout
app.layout = html.Div(
    [
        # Auto-refresh component
        dcc.Interval(id="hfq-refresh-interval", interval=1000, n_intervals=0),  # 1 second refresh
        # Header Section
        html.Div(
            [
                html.Div(
                    [
                        html.H1(
                            "🚀 HFQ Trading Simulation",
                            style={
                                "margin": "0",
                                "color": "white",
                                "fontSize": "2.8rem",
                                "fontWeight": "700",
                                "textShadow": "0 2px 4px rgba(0,0,0,0.3)",
                            },
                        ),
                        html.P(
                            "Real-time Market Data & Trade Execution Monitor",
                            style={
                                "margin": "8px 0 0 0",
                                "color": "#e2e8f0",
                                "fontSize": "1.2rem",
                                "fontWeight": "400",
                            },
                        ),
                        html.Div(
                            id="hfq-connection-status",
                            className="status-pulse",
                            style={"marginTop": "16px", "fontSize": "1.1rem"},
                        ),
                    ],
                    style={"textAlign": "center"},
                )
            ],
            style={
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "color": "white",
                "padding": "40px 30px",
                "borderRadius": "20px",
                "marginBottom": "32px",
                "boxShadow": "0 10px 25px rgba(0, 0, 0, 0.15)",
            },
        ),
        # Statistics Cards Row
        html.Div(
            [
                html.H2(
                    "📊 Live Statistics",
                    style={
                        "textAlign": "center",
                        "marginBottom": "24px",
                        "color": "#1f2937",
                        "fontSize": "1.8rem",
                        "fontWeight": "600",
                    },
                ),
                html.Div(id="hfq-stats-container", style={"textAlign": "center"}),
            ],
            style={"marginBottom": "40px"},
        ),
        # Charts Section
        html.Div(
            [
                html.H2(
                    "📈 Market Analysis",
                    style={
                        "textAlign": "center",
                        "marginBottom": "32px",
                        "color": "#1f2937",
                        "fontSize": "1.8rem",
                        "fontWeight": "600",
                    },
                ),
                html.Div(
                    [
                        # Price Chart
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3(
                                            "💹 Price Movement (OHLC)",
                                            style={
                                                "textAlign": "center",
                                                "marginBottom": "20px",
                                                "color": "#374151",
                                                "fontSize": "1.3rem",
                                                "fontWeight": "600",
                                            },
                                        ),
                                        dcc.Graph(id="hfq-price-chart", style={"height": "420px"}),
                                    ]
                                )
                            ],
                            style={
                                "width": "49%",
                                "display": "inline-block",
                                "backgroundColor": "white",
                                "padding": "24px",
                                "borderRadius": "16px",
                                "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.07)",
                                "marginRight": "2%",
                            },
                        ),
                        # Volume Chart
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3(
                                            "📊 Trading Volume",
                                            style={
                                                "textAlign": "center",
                                                "marginBottom": "20px",
                                                "color": "#374151",
                                                "fontSize": "1.3rem",
                                                "fontWeight": "600",
                                            },
                                        ),
                                        dcc.Graph(id="hfq-volume-chart", style={"height": "420px"}),
                                    ]
                                )
                            ],
                            style={
                                "width": "49%",
                                "display": "inline-block",
                                "backgroundColor": "white",
                                "padding": "24px",
                                "borderRadius": "16px",
                                "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.07)",
                            },
                        ),
                    ]
                ),
            ],
            style={"marginBottom": "40px"},
        ),
        # Data Tables Section
        html.Div(
            [
                html.H2(
                    "📋 Market Data Tables",
                    style={
                        "textAlign": "center",
                        "marginBottom": "32px",
                        "color": "#1f2937",
                        "fontSize": "1.8rem",
                        "fontWeight": "600",
                    },
                ),
                html.Div(
                    [
                        # Candles Table
                        html.Div(
                            [
                                html.H3(
                                    "🕯️ Market Candles",
                                    style={
                                        "textAlign": "center",
                                        "marginBottom": "20px",
                                        "color": "#374151",
                                        "fontSize": "1.3rem",
                                        "fontWeight": "600",
                                    },
                                ),
                                html.Div(id="hfq-candles-table"),
                            ],
                            style={
                                "width": "49%",
                                "display": "inline-block",
                                "backgroundColor": "white",
                                "padding": "24px",
                                "borderRadius": "16px",
                                "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.07)",
                                "marginRight": "2%",
                            },
                        ),
                        # Trades Table
                        html.Div(
                            [
                                html.H3(
                                    "💼 Trade Executions",
                                    style={
                                        "textAlign": "center",
                                        "marginBottom": "20px",
                                        "color": "#374151",
                                        "fontSize": "1.3rem",
                                        "fontWeight": "600",
                                    },
                                ),
                                html.Div(id="hfq-trades-table"),
                            ],
                            style={
                                "width": "49%",
                                "display": "inline-block",
                                "backgroundColor": "white",
                                "padding": "24px",
                                "borderRadius": "16px",
                                "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.07)",
                            },
                        ),
                    ]
                ),
            ]
        ),
    ],
    style={
        "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "backgroundColor": "#f8fafc",
        "minHeight": "100vh",
        "padding": "32px",
    },
)


# Main callback - handles all updates
@app.callback(
    [
        Output("hfq-connection-status", "children"),
        Output("hfq-stats-container", "children"),
        Output("hfq-price-chart", "figure"),
        Output("hfq-volume-chart", "figure"),
        Output("hfq-candles-table", "children"),
        Output("hfq-trades-table", "children"),
    ],
    Input("hfq-refresh-interval", "n_intervals"),
)
def update_hfq_dashboard(n_intervals):
    """Main dashboard update function."""

    try:
        # Get state service and data
        state_service = get_state_service()
        state = state_service.state

        candles_data = []
        trades_data = []
        candles_total = 0
        trades_total = 0

        # Extract data from state
        with state.with_dict_view(snapshot=True) as view:
            # Get candles data
            with view.at("canldes").with_list_view() as candles:
                candles_total = candles.length()
                if candles_total > 0:
                    start_idx = max(0, candles_total - 30)  # Last 30 candles
                    candles_data = [candles.get(i) for i in range(start_idx, candles_total)]

            # Get trades data
            with view.at("trades").with_list_view() as trades:
                trades_total = trades.length()
                if trades_total > 0:
                    start_idx = max(0, trades_total - 30)  # Last 30 trades
                    trades_data = [trades.get(i) for i in range(start_idx, trades_total)]

        # Create connection status
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if candles_data or trades_data:
            status = html.Div(
                [
                    html.Span("🟢 ", style={"fontSize": "1.4rem"}),
                    html.Span(f"Live • {current_time} • Update #{n_intervals}"),
                ]
            )
        else:
            status = html.Div(
                [
                    html.Span("🟡 ", style={"fontSize": "1.4rem"}),
                    html.Span(f"Connected • Waiting for data • {current_time}"),
                ]
            )

        # Calculate statistics
        latest_candle = candles_data[-1] if candles_data else None
        avg_volume = (
            sum(c.get("volume", 0) for c in candles_data) / len(candles_data) if candles_data else 0
        )

        # Calculate price change percentage
        price_change = 0
        if len(candles_data) >= 2:
            price_change = (
                (candles_data[-1]["close"] - candles_data[0]["open"]) / candles_data[0]["open"]
            ) * 100

        # Create statistics cards
        stats_cards = html.Div(
            [
                create_stat_card(
                    "Total Candles",
                    f"{candles_total:,}",
                    f"Showing last {min(30, candles_total)}",
                    "#059669",
                    "🕯️",
                ),
                create_stat_card(
                    "Total Trades",
                    f"{trades_total:,}",
                    f"Showing last {min(30, trades_total)}",
                    "#dc2626",
                    "💹",
                ),
                create_stat_card(
                    "Current Price",
                    f"${latest_candle['close']:.2f}" if latest_candle else "N/A",
                    "Latest close price",
                    "#3b82f6",
                    "💰",
                    price_change if abs(price_change) > 0.01 else None,
                ),
                create_stat_card(
                    "Avg Volume",
                    f"{avg_volume:,.0f}" if avg_volume else "N/A",
                    "Per candle period",
                    "#7c3aed",
                    "📊",
                ),
            ]
        )

        # Create price chart
        price_fig = go.Figure()
        if candles_data:
            df = pd.DataFrame(candles_data)
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")

            price_fig.add_trace(
                go.Candlestick(
                    x=df["datetime"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name="OHLC",
                    increasing_line_color="#10b981",
                    decreasing_line_color="#ef4444",
                    increasing_fillcolor="#10b981",
                    decreasing_fillcolor="#ef4444",
                )
            )

            price_fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Price ($)",
                template="plotly_white",
                showlegend=False,
                margin=dict(l=50, r=30, t=30, b=50),
                font=dict(family="Inter, sans-serif", size=11),
                plot_bgcolor="rgba(248,250,252,0.8)",
                xaxis=dict(gridcolor="rgba(0,0,0,0.1)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0.1)"),
            )
        else:
            price_fig.add_annotation(
                text="📈 Waiting for price data...",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="#6b7280"),
            )
            price_fig.update_layout(template="plotly_white", plot_bgcolor="rgba(248,250,252,0.8)")

        # Create volume chart
        volume_fig = go.Figure()
        if candles_data:
            df = pd.DataFrame(candles_data)
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")

            volume_fig.add_trace(
                go.Bar(
                    x=df["datetime"],
                    y=df["volume"],
                    name="Volume",
                    marker_color="rgba(124, 58, 237, 0.8)",
                    marker_line_color="rgba(124, 58, 237, 1)",
                    marker_line_width=1.5,
                )
            )

            volume_fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Volume",
                template="plotly_white",
                showlegend=False,
                margin=dict(l=50, r=30, t=30, b=50),
                font=dict(family="Inter, sans-serif", size=11),
                plot_bgcolor="rgba(248,250,252,0.8)",
                xaxis=dict(gridcolor="rgba(0,0,0,0.1)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0.1)"),
            )
        else:
            volume_fig.add_annotation(
                text="📊 Waiting for volume data...",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="#6b7280"),
            )
            volume_fig.update_layout(template="plotly_white", plot_bgcolor="rgba(248,250,252,0.8)")

        # Create candles table
        if candles_data:
            candles_df = pd.DataFrame(candles_data)
            candles_df["time"] = candles_df["timestamp"].apply(format_timestamp)
            candles_df["change"] = candles_df["close"] - candles_df["open"]
            candles_df["change_pct"] = (candles_df["change"] / candles_df["open"] * 100).round(2)

            candles_table = dash_table.DataTable(
                data=candles_df[
                    ["time", "open", "high", "low", "close", "volume", "change_pct"]
                ].to_dict("records"),
                columns=[
                    {"name": "Time", "id": "time"},
                    {
                        "name": "Open",
                        "id": "open",
                        "type": "numeric",
                        "format": {"specifier": ".2f"},
                    },
                    {
                        "name": "High",
                        "id": "high",
                        "type": "numeric",
                        "format": {"specifier": ".2f"},
                    },
                    {"name": "Low", "id": "low", "type": "numeric", "format": {"specifier": ".2f"}},
                    {
                        "name": "Close",
                        "id": "close",
                        "type": "numeric",
                        "format": {"specifier": ".2f"},
                    },
                    {
                        "name": "Volume",
                        "id": "volume",
                        "type": "numeric",
                        "format": {"specifier": ",.0f"},
                    },
                    {
                        "name": "Change %",
                        "id": "change_pct",
                        "type": "numeric",
                        "format": {"specifier": ".2f"},
                    },
                ],
                style_cell={
                    "textAlign": "center",
                    "fontSize": "12px",
                    "padding": "10px 8px",
                    "fontFamily": "Inter, sans-serif",
                },
                style_data_conditional=[
                    {
                        "if": {"filter_query": "{change_pct} > 0"},
                        "backgroundColor": "#ecfdf5",
                        "color": "#065f46",
                        "fontWeight": "600",
                    },
                    {
                        "if": {"filter_query": "{change_pct} < 0"},
                        "backgroundColor": "#fef2f2",
                        "color": "#991b1b",
                        "fontWeight": "600",
                    },
                ],
                style_header={
                    "backgroundColor": "#f8fafc",
                    "fontWeight": "bold",
                    "border": "1px solid #e2e8f0",
                    "color": "#374151",
                },
                page_size=15,
                style_table={"overflowX": "auto"},
            )
        else:
            candles_table = html.Div(
                [
                    html.P(
                        "📭 No candle data available",
                        style={"textAlign": "center", "color": "#6b7280", "fontSize": "1.1rem"},
                    )
                ]
            )

        # Create trades table
        if trades_data:
            trades_df = pd.DataFrame(trades_data)
            trades_df["time"] = trades_df["timestamp"].apply(format_timestamp)

            trades_table = dash_table.DataTable(
                data=trades_df[["time", "price", "volume"]].to_dict("records"),
                columns=[
                    {"name": "Time", "id": "time"},
                    {
                        "name": "Price",
                        "id": "price",
                        "type": "numeric",
                        "format": {"specifier": ".2f"},
                    },
                    {
                        "name": "Volume",
                        "id": "volume",
                        "type": "numeric",
                        "format": {"specifier": ".2f"},
                    },
                ],
                style_cell={
                    "textAlign": "center",
                    "fontSize": "12px",
                    "padding": "10px 8px",
                    "fontFamily": "Inter, sans-serif",
                },
                style_header={
                    "backgroundColor": "#f8fafc",
                    "fontWeight": "bold",
                    "border": "1px solid #e2e8f0",
                    "color": "#374151",
                },
                page_size=15,
                style_table={"overflowX": "auto"},
            )
        else:
            trades_table = html.Div(
                [
                    html.P(
                        "📭 No trade data available",
                        style={"textAlign": "center", "color": "#6b7280", "fontSize": "1.1rem"},
                    )
                ]
            )

        return status, stats_cards, price_fig, volume_fig, candles_table, trades_table

    except Exception as e:
        # Error handling with graceful fallback
        error_msg = f"⚠️ Error: {str(e)}"
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Error loading data", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
        )
        empty_fig.update_layout(template="plotly_white")

        return (
            html.Div(error_msg, style={"color": "#ef4444"}),
            html.Div("Error loading stats"),
            empty_fig,
            empty_fig,
            html.Div("Error loading candles data"),
            html.Div("Error loading trades data"),
        )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app.run(debug=False, port=8051)  # Using different port to avoid conflicts
