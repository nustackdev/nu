"""WebSocket server for nudle."""

from __future__ import annotations

import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI(title="nudle")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """Handle WebSocket connections."""
    await ws.accept()
    await ws.send_text(json.dumps({"type": "hello", "message": "nudle connected"}))
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
