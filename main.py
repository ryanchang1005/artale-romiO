from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


TOTAL_LAYERS = 10
TOTAL_POSITIONS = 4
ROOM_PASSWORD = "123456"


DEFAULT_COLORS = {
    "red": "#ef4444",
    "green": "#22c55e",
    "blue": "#3b82f6",
    "yellow": "#eab308",
    "purple": "#a855f7",
    "orange": "#f97316",
    "pink": "#ec4899",
    "cyan": "#06b6d4",
}

ALLOWED_COLORS = set(DEFAULT_COLORS.values())


def normalize_color(raw_color: str | None) -> str:
    if raw_color in ALLOWED_COLORS:
        return raw_color
    return ""


@dataclass
class PlayerState:
    id: str
    color: str | None
    answer: list[int | None]


class RoomState:
    def __init__(self) -> None:
        self.players: dict[str, PlayerState] = {}

    def ensure_player(self, player_id: str) -> PlayerState:
        if player_id not in self.players:
            self.players[player_id] = PlayerState(
                id=player_id,
                color=None,
                answer=[None for _ in range(TOTAL_LAYERS)],
            )
        return self.players[player_id]

    def is_player_id_available(self, player_id: str) -> bool:
        return player_id not in self.players

    def set_player_color(self, player_id: str, color: str | None) -> bool:
        player = self.ensure_player(player_id)
        chosen = normalize_color(color)
        if not chosen:
            return False

        for other in self.players.values():
            if other.id != player_id and other.color == chosen:
                return False

        player.color = chosen
        return True

    def set_player_choice(
        self, player_id: str, layer: int, position: int, overwrite: bool = False
    ) -> None:
        if not (0 <= layer < TOTAL_LAYERS):
            return
        if not (1 <= position <= TOTAL_POSITIONS):
            return

        player = self.ensure_player(player_id)
        if not player.color:
            return

        if overwrite:
            for other in self.players.values():
                if other.id != player_id and other.answer[layer] == position:
                    other.answer[layer] = None

        player.answer[layer] = position

    def clear_player_choice(self, player_id: str, layer: int) -> None:
        if not (0 <= layer < TOTAL_LAYERS):
            return
        player = self.ensure_player(player_id)
        player.answer[layer] = None

    def remove_player(self, player_id: str) -> None:
        if player_id in self.players:
            del self.players[player_id]

    def clear_all_answers(self) -> None:
        for player in self.players.values():
            player.answer = [None for _ in range(TOTAL_LAYERS)]

    def to_payload(self) -> dict[str, Any]:
        board: list[list[list[dict[str, str]]]] = [
            [[] for _ in range(TOTAL_POSITIONS)] for _ in range(TOTAL_LAYERS)
        ]

        for player in self.players.values():
            for layer_idx, pos in enumerate(player.answer):
                if pos is None:
                    continue
                board[layer_idx][pos - 1].append({"id": player.id, "color": player.color})

        players = [
            {
                "id": p.id,
                "color": p.color,
                "answer": p.answer,
            }
            for p in sorted(self.players.values(), key=lambda x: x.id)
        ]

        return {
            "type": "state",
            "layers": TOTAL_LAYERS,
            "positions": TOTAL_POSITIONS,
            "players": players,
            "board": board,
        }


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, payload: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False))
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


app = FastAPI(title="Artale Level Helper")
templates = Jinja2Templates(directory="templates")
room_state = RoomState()
manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {})


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    player_id: str | None = None
    await websocket.send_text(
        json.dumps({"type": "auth_required", "message": "請先輸入密碼與玩家 ID"}, ensure_ascii=False)
    )

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            action = data.get("action")

            if action == "auth":
                password = str(data.get("password", ""))
                requested_id = str(data.get("player_id", "")).strip()[:8]

                if password != ROOM_PASSWORD:
                    await websocket.send_text(
                        json.dumps({"type": "auth_error", "message": "密碼錯誤"}, ensure_ascii=False)
                    )
                    continue

                if not requested_id:
                    await websocket.send_text(
                        json.dumps({"type": "auth_error", "message": "請輸入玩家 ID"}, ensure_ascii=False)
                    )
                    continue

                if not room_state.is_player_id_available(requested_id):
                    await websocket.send_text(
                        json.dumps({"type": "auth_error", "message": "此 ID 已被使用"}, ensure_ascii=False)
                    )
                    continue

                player_id = requested_id
                room_state.ensure_player(player_id)

                payload = room_state.to_payload()
                payload["type"] = "auth_ok"
                payload["self_id"] = player_id
                await websocket.send_text(json.dumps(payload, ensure_ascii=False))
                await manager.broadcast_json(room_state.to_payload())
                continue

            if not player_id:
                await websocket.send_text(
                    json.dumps({"type": "auth_error", "message": "請先完成登入"}, ensure_ascii=False)
                )
                continue

            if action == "set_color":
                room_state.set_player_color(player_id=player_id, color=data.get("color"))
                await manager.broadcast_json(room_state.to_payload())
            elif action == "pick":
                layer = int(data.get("layer", -1))
                position = int(data.get("position", -1))
                overwrite = bool(data.get("overwrite", False))
                room_state.set_player_choice(
                    player_id=player_id,
                    layer=layer,
                    position=position,
                    overwrite=overwrite,
                )
                await manager.broadcast_json(room_state.to_payload())
            elif action == "unpick":
                layer = int(data.get("layer", -1))
                room_state.clear_player_choice(player_id=player_id, layer=layer)
                await manager.broadcast_json(room_state.to_payload())
            elif action == "clear":
                room_state.clear_all_answers()
                await manager.broadcast_json(room_state.to_payload())
    except (WebSocketDisconnect, RuntimeError):
        if player_id:
            room_state.remove_player(player_id)
        manager.disconnect(websocket)
        await manager.broadcast_json(room_state.to_payload())
    except Exception:
        if player_id:
            room_state.remove_player(player_id)
        manager.disconnect(websocket)
        await manager.broadcast_json(room_state.to_payload())
