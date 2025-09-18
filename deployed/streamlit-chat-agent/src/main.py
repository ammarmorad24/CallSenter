import asyncio
import websockets
import json
import random

async def agent_chat(websocket, user_input):
    agent_id = f"agent_{random.randint(1000, 9999)}"
    uri = f"ws://127.0.0.1:8000/ws/agent?user_id={agent_id}"

    try:
        async with websockets.connect(uri) as websocket:
            print(f"🌟 Agent Client Starting")
            print(f"👤 Agent ID: {agent_id}")
            print(f"🔗 Connecting to: {uri}")
            print("✅ Connected! Waiting for customer...")

            while True:
                if user_input:
                    message = user_input
                    await websocket.send(json.dumps({
                        "msg": message,
                        "lang": "ar"
                    }))
                    print(f"📤 Sent: {message}")
                    user_input = None  # Reset user input after sending

                message = await websocket.recv()
                print(f"\n📨 Raw received: {message}")

                try:
                    data = json.loads(message)
                    if "msg" in data:
                        translated = data["msg"]
                        print(f"👤 Customer: {translated}")
                except json.JSONDecodeError:
                    print(f"📨 Customer: {message}")

    except Exception as e:
        print(f"❌ Connection error: {e}")

def start_chat(user_input):
    asyncio.run(agent_chat(websockets.connect("ws://127.0.0.1:8000/ws/agent"), user_input))
