# customer_client.py
import asyncio
import websockets
import json

async def customer_chat():
    uri = "ws://CHAT_EC2_PUBLIC_IP:8000/ws/customer"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"msg": "Hello!", "lang": "en"}))
        while True:
            reply = await ws.recv()
            print("Agent:", reply)

asyncio.run(customer_chat())
