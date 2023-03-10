from fastapi import FastAPI, Request, WebSocket
from fastapi.templating import Jinja2Templates
from sqlalchemy import cast, extract, func, select, update, delete, exists, or_, not_, and_, Integer
from starlette.websockets import WebSocketDisconnect

from models.models import Matrix, User
from typing import List

from models.base import SessionLocal

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint( vk_id: str  websocket: WebSocket):
    # user = list(db.scalars(select(User).where(User.vk_id == vk_id)))

    try:
        while True:
            "vk_id, color , x_position, x_position "
            data = await websocket.receive_json()

            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
