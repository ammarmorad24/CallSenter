# agent_client.py
import asyncio
import websockets
import json

async def agent_chat():
    uri = "ws://CHAT_EC2_PUBLIC_IP:8000/ws/agent"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"msg": "اهلا!", "lang": "ar"}))
        while True:
            reply = await ws.recv()
            print("Agent:", reply)

asyncio.run(agent_chat())
