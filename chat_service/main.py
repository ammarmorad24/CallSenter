# chat_service/main.py - FIXED VERSION
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
import httpx
import json
from translate import translate_text, translate_ar_to_en, translate_en_to_ar
import datetime
import uuid

app = FastAPI()

# Store active connections by role
active_connections = {
    "customer": [],
    "agent": []
}

# Store conversation pairs
conversation_pairs = {}  # {conversation_id: {"customer": ws, "agent": ws}}
chat_history = {}
conversation_data = {}

# Configure your n8n webhook URL
N8N_WEBHOOK_URL = "https://ammar202220216.app.n8n.cloud/webhook-test/1a86a8b4-9bab-46e3-a412-4989779390da"
N8N_ENABLED = True

@app.get("/")
async def root():
    return {"message": "CallSenter Chat Service is running"}

@app.get("/status")
async def status():
    return {
        "active_customers": len(active_connections["customer"]),
        "active_agents": len(active_connections["agent"]),
        "active_conversations": len(conversation_pairs)
    }

@app.get("/test-n8n")
async def test_n8n_connection():
    """Test endpoint to verify n8n connectivity"""
    if not N8N_ENABLED:
        return {"status": "n8n disabled in settings"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                N8N_WEBHOOK_URL, 
                json={"test": "connection"}
            )
            return {
                "status": "success", 
                "status_code": response.status_code,
                "response": response.text
            }
    except Exception as e:
        return {"status": "error", "message": str(e), "error_type": type(e).__name__}

def find_or_create_conversation(role, ws, user_id, language=None):
    """Find an available conversation or create a new one"""
    
    # Look for existing conversation waiting for a partner
    for conv_id, pair in conversation_pairs.items():
        if role == "customer" and "agent" in pair and "customer" not in pair:
            # Agent waiting for customer
            pair["customer"] = ws
            conversation_data[conv_id]["customer_id"] = user_id
            if language:
                conversation_data[conv_id]["customer_language"] = language
            return conv_id
        elif role == "agent" and "customer" in pair and "agent" not in pair:
            # Customer waiting for agent
            pair["agent"] = ws
            conversation_data[conv_id]["agent_id"] = user_id
            return conv_id
    
    # No existing conversation found, create new one
    conversation_id = str(uuid.uuid4())[:8]
    conversation_pairs[conversation_id] = {role: ws}
    
    # Initialize conversation data
    conversation_data[conversation_id] = {
        "conversation_id": conversation_id,
        "customer_id": user_id if role == "customer" else None,
        "agent_id": user_id if role == "agent" else None,
        "start_time": datetime.datetime.now(),
        "end_time": None,
        "customer_language": language if role == "customer" else None
    }
    
    # Initialize chat history
    chat_history[conversation_id] = []
    
    return conversation_id

async def notify_connection_status(conversation_id):
    """Notify both parties about connection status"""
    pair = conversation_pairs.get(conversation_id)
    if not pair:
        return
        
    if "customer" in pair and "agent" in pair:
        # Both connected
        if "customer" in pair:
            await pair["customer"].send_text(json.dumps({
                "system_message": "Agent connected! You can start chatting.",
                "status": "both_connected"
            }))
        if "agent" in pair:
            await pair["agent"].send_text(json.dumps({
                "system_message": "Customer connected! You can start chatting.",
                "status": "both_connected"
            }))
    else:
        # Waiting for partner
        role = list(pair.keys())[0]
        waiting_for = "agent" if role == "customer" else "customer"
        await pair[role].send_text(json.dumps({
            "system_message": f"Waiting for {waiting_for} to connect...",
            "status": "waiting"
        }))

@app.websocket("/ws/{role}")
async def chat_endpoint(
    ws: WebSocket, 
    role: str,
    user_id: str = Query(None),
    language: str = Query("en")
):
    await ws.accept()
    
    print(f"New {role} connected: {user_id}")
    
    # Add to active connections
    active_connections[role].append(ws)
    
    # Find or create conversation
    conversation_id = find_or_create_conversation(role, ws, user_id, language)
    
    print(f"Conversation {conversation_id}: {role} {user_id} joined")
    
    # Notify about connection status
    await notify_connection_status(conversation_id)
    
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            
            print(f"Received from {role} {user_id}: {msg}")
            
            # Check if this is an end_chat message
            if msg.get("end_chat") == True:
                print(f"Chat ended by {role} {user_id}")
                
                # Set end time
                if conversation_id in conversation_data:
                    conversation_data[conversation_id]["end_time"] = datetime.datetime.now()
                
                # Notify the other participant
                pair = conversation_pairs.get(conversation_id)
                if pair:
                    other_role = "agent" if role == "customer" else "customer"
                    if other_role in pair:
                        await pair[other_role].send_text(json.dumps({
                            "system_message": "Chat has ended by the other party",
                            "end_chat": True
                        }))
                
                # Send to n8n if enabled
                if N8N_ENABLED and conversation_id in conversation_data:
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            payload = {
                                **conversation_data[conversation_id],
                                "event": "chat_ended",
                                "ended_by": role,
                                "chat_history": chat_history.get(conversation_id, []),
                            }
                            
                            # Convert datetime objects to ISO format strings
                            payload["start_time"] = payload["start_time"].isoformat()
                            if payload["end_time"]:
                                payload["end_time"] = payload["end_time"].isoformat()
                            
                            response = await client.post(N8N_WEBHOOK_URL, json=payload)
                            print(f"n8n webhook response: {response.status_code}")
                    except Exception as e:
                        print(f"Failed to send to n8n: {str(e)}")
                
                # Clean up
                cleanup_conversation(conversation_id)
                break
            
            # Process regular messages
            if "msg" in msg:
                pair = conversation_pairs.get(conversation_id)
                if not pair:
                    print(f"No conversation found for {conversation_id}")
                    continue
                
                # Check if both parties are connected
                other_role = "agent" if role == "customer" else "customer"
                if other_role not in pair:
                    await ws.send_text(json.dumps({
                        "system_message": f"Waiting for {other_role} to connect...",
                        "status": "waiting"
                    }))
                    continue
                
                # Update customer language if detected
                if role == "customer" and "lang" in msg and conversation_id in conversation_data:
                    conversation_data[conversation_id]["customer_language"] = msg.get("lang", "en")
                
                # Translate message
                source_lang = msg.get("lang", "en")
                target_lang = "ar" if role == "customer" else "en"
                
                try:
                    translated = translate_text(msg["msg"], source_lang, target_lang)
                    print(f"Translated '{msg['msg']}' from {source_lang} to {target_lang}: '{translated}'")
                except Exception as e:
                    print(f"Translation error: {e}")
                    translated = msg["msg"]  # Fall back to original
                
                # Store message in chat history
                if conversation_id in chat_history:
                    chat_history[conversation_id].append({
                        "role": role,
                        "original": msg["msg"],
                        "translated": translated,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "language": source_lang
                    })
                
                # Send to the other participant
                try:
                    await pair[other_role].send_text(json.dumps({
                        "msg": translated,
                        "original": msg["msg"],
                        "from": role
                    }))
                    print(f"Sent to {other_role}: {translated}")
                except Exception as e:
                    print(f"Error sending to {other_role}: {e}")

    except WebSocketDisconnect:
        print(f"{role} {user_id} disconnected")
        cleanup_connection(ws, role, conversation_id)
    except Exception as e:
        print(f"Error in websocket for {role} {user_id}: {e}")
        cleanup_connection(ws, role, conversation_id)

def cleanup_connection(ws, role, conversation_id):
    """Clean up when a connection is closed"""
    import asyncio
    
    # Remove from active connections
    if ws in active_connections[role]:
        active_connections[role].remove(ws)
    
    # Handle conversation cleanup
    if conversation_id in conversation_pairs:
        pair = conversation_pairs[conversation_id]
        
        # Remove this connection from the pair
        if role in pair and pair[role] == ws:
            del pair[role]
        
        # If conversation is now empty, clean it up completely
        if not pair:
            cleanup_conversation(conversation_id)
        else:
            # Notify remaining participant
            remaining_role = list(pair.keys())[0]
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(pair[remaining_role].send_text(json.dumps({
                    "system_message": f"{role.title()} disconnected",
                    "status": "partner_disconnected"
                })))
            except Exception as e:
                print(f"Error notifying remaining participant: {e}")

def cleanup_conversation(conversation_id):
    """Completely clean up a conversation"""
    if conversation_id in conversation_pairs:
        del conversation_pairs[conversation_id]
    if conversation_id in chat_history:
        del chat_history[conversation_id]
    if conversation_id in conversation_data:
        del conversation_data[conversation_id]
    print(f"Cleaned up conversation {conversation_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
