# app/chats/connection_manager.py
from typing import Dict, List, Any
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}  # chat_id: [WebSocket]

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        print(
            f"WebSocket connected to chat {chat_id}. Total connections for chat: {len(self.active_connections[chat_id])}")

    def disconnect(self, websocket: WebSocket, chat_id: int):
        if chat_id in self.active_connections:
            if websocket in self.active_connections[chat_id]:
                self.active_connections[chat_id].remove(websocket)
                print(f"WebSocket disconnected from chat {chat_id}.")
                if not self.active_connections[chat_id]:
                    del self.active_connections[chat_id]
                    print(f"No more connections for chat {chat_id}, removing chat entry.")
            else:
                print(f"Attempted to disconnect a non-existent websocket from chat {chat_id}.")
        else:
            print(f"Attempted to disconnect websocket from non-existent chat entry {chat_id}.")

    async def broadcast_to_chat(self, message_data: Dict[str, Any], chat_id: int):
        if chat_id in self.active_connections:
            print(f"Broadcasting to chat {chat_id}: {message_data}")
            disconnected_sockets = []
            for connection in self.active_connections[chat_id]:
                try:
                    await connection.send_json(message_data)
                except Exception as e:  # WebSocketException or ConnectionClosed
                    print(f"Error sending message to a websocket in chat {chat_id}: {e}. Marking for removal.")
                    disconnected_sockets.append(connection)

            # Видалення "мертвих" з'єднань
            for sock in disconnected_sockets:
                self.disconnect(sock, chat_id)


manager = ConnectionManager()