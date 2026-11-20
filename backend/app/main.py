from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from . import db
from .config import load_config
from .game import SessionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("experiment")

config = load_config()
manager = SessionManager(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    log.info("loaded config: %s", config.as_dict())
    yield
    await db.close()


app = FastAPI(title="Group Decision Experiment", lifespan=lifespan)


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/api/join")
async def join() -> dict:
    """Takes a seat for a new human participant. The token identifies the
    participant on the WebSocket; the player label comes with the first state."""
    token = await manager.join()
    return {"token": token}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = ""):
    await ws.accept()
    found = manager.lookup(token)
    if found is None:
        await ws.close(code=4401, reason="unknown session")
        return

    session, label = found
    session.attach(label, ws)
    await session.send_state(label)
    try:
        while True:
            try:
                data = await ws.receive_json()
            except ValueError:
                await ws.send_json({"type": "error", "message": "Invalid message."})
                continue

            action = data.get("type") if isinstance(data, dict) else None
            if action == "chat":
                error = await session.post_chat(label, str(data.get("text", "")))
            elif action == "vote":
                error = await session.cast_vote(label, str(data.get("target", "")))
            else:
                error = "Unknown action."

            if error:
                await ws.send_json({"type": "error", "message": error})
    except WebSocketDisconnect:
        pass
    finally:
        session.detach(label, ws)
