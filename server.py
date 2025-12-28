import asyncio
import websockets
import json
import os

clients = {}

async def handler(websocket):
    try:
        data = json.loads(await websocket.recv())
        username = data["username"]
        clients[username] = websocket

        # Send updated online users list
        await broadcast_users()

        async for message in websocket:
            msg = json.loads(message)
            to_user = msg["to"]

            if to_user in clients:
                await clients[to_user].send(json.dumps({
                    "type": "message",
                    "from": username,
                    "text": msg["text"],
                    "time": msg["time"]
                }))
    except:
        pass
    finally:
        clients.pop(username, None)
        await broadcast_users()

async def broadcast_users():
    users = list(clients.keys())
    for ws in clients.values():
        await ws.send(json.dumps({
            "type": "online_users",
            "users": users
        }))

async def main():
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()

asyncio.run(main())
