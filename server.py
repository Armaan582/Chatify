import asyncio
import json
import os
import websockets

# Store connected users
# key   = username
# value = websocket connection
clients = {}

# -----------------------------
# Helper: Broadcast online users
# -----------------------------
async def broadcast_users():
    users = list(clients.keys())
    payload = json.dumps({
        "type": "online_users",
        "users": users
    })

    disconnected = []
    for username, ws in clients.items():
        try:
            await ws.send(payload)
        except:
            disconnected.append(username)

    # Clean up dead connections
    for user in disconnected:
        clients.pop(user, None)


# -----------------------------
# Main WebSocket Handler
# -----------------------------
async def handler(websocket):
    username = None

    try:
        # First message must be username
        init_data = await websocket.recv()
        data = json.loads(init_data)
        username = data.get("username")

        if not username:
            return

        # Save connection
        clients[username] = websocket
        print(f"[CONNECTED] {username}")

        # Notify everyone
        await broadcast_users()

        # Listen for incoming messages
        async for raw_msg in websocket:
            try:
                msg = json.loads(raw_msg)
                msg_type = msg.get("type")
                to_user = msg.get("to")

                if not to_user or to_user not in clients:
                    continue

                # -----------------------------
                # TEXT MESSAGE
                # -----------------------------
                if msg_type == "message":
                    await clients[to_user].send(json.dumps({
                        "type": "message",
                        "from": username,
                        "text": msg.get("text"),
                        "time": msg.get("time")
                    }))

                # -----------------------------
                # TYPING INDICATOR
                # -----------------------------
                elif msg_type == "typing":
                    await clients[to_user].send(json.dumps({
                        "type": "typing",
                        "from": username
                    }))

            except Exception as e:
                print("Message error:", e)

    except Exception as e:
        print("Connection error:", e)

    finally:
        # Remove user on disconnect
        if username and username in clients:
            clients.pop(username, None)
            print(f"[DISCONNECTED] {username}")
            await broadcast_users()


# -----------------------------
# Server Bootstrap
# -----------------------------
async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 Server running on port {port}")

    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
