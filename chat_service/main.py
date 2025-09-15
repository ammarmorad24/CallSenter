# chat_service.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx
import json
from translate import translate_text, translate_ar_to_en, translate_en_to_ar

app = FastAPI()
connections = {}

N8N_WEBHOOK_URL = "http://N8N_SERVER:5678/webhook/chat"

@app.websocket("/ws/{role}")
async def chat_endpoint(ws: WebSocket, role: str):
    await ws.accept()
    connections[role] = ws
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            # --- Translation stub (replace with your model) ---
            translated = translate_text(msg["msg"], msg.get("lang", "en"), 
                                        "ar" if role=="customer" else "en")

            # Send to opposite role
            other = "agent" if role == "customer" else "customer"
            if other in connections:
                await connections[other].send_text(translated)

            # Send webhook to n8n
            async with httpx.AsyncClient() as client:
                await client.post(N8N_WEBHOOK_URL, json={
                    "from": role,
                    "text": msg["msg"],
                    "translated": translated,
                    "lang": msg.get("lang")
                })

    except WebSocketDisconnect:
        connections.pop(role, None)


def fake_translate(text, src, tgt):
    return f"[{tgt}] {text[::-1]}"
