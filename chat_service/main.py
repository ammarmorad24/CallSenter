# chat_service.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
import httpx
import json
from translate import translate_text, translate_ar_to_en, translate_en_to_ar
import datetime
import uuid

app = FastAPI()
connections = {}
chat_history = {}  # Store chat history for each conversation
conversation_data = {}  # Store metadata about conversations

# Configure your n8n webhook URL - update this to your actual n8n URL
N8N_WEBHOOK_URL = "https://ammar202220216.app.n8n.cloud/webhook-test/1a86a8b4-9bab-46e3-a412-4989779390da"
N8N_ENABLED = True  # Set to False for testing without n8n

# Add this function to test your n8n connection
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

@app.websocket("/ws/{role}")
async def chat_endpoint(
    ws: WebSocket, 
    role: str,
    user_id: str = Query(None),
    language: str = Query("en")
):
    await ws.accept()
    
    # Generate conversation ID if this is a new conversation
    conversation_id = str(uuid.uuid4())[:8]  # Short UUID for conversation ID
    current_time = datetime.datetime.now()
    
    # Store connection
    connections[role] = {
        "ws": ws,
        "user_id": user_id,
        "language": language
    }
    
    # Initialize conversation data
    if role == "customer":
        conversation_data[conversation_id] = {
            "conversation_id": conversation_id,
            "customer_id": user_id,
            "agent_id": None,  # Will be set when agent connects
            "start_time": current_time,
            "end_time": None,
            "customer_language": language
        }
    else:  # Agent
        # Find existing conversation or create new one
        if not conversation_data:
            conversation_data[conversation_id] = {
                "conversation_id": conversation_id,
                "customer_id": None,  # Will be set when customer connects
                "agent_id": user_id,
                "start_time": current_time,
                "end_time": None,
                "customer_language": None
            }
        else:
            # Get the first available conversation
            conversation_id = next(iter(conversation_data))
            conversation_data[conversation_id]["agent_id"] = user_id
    
    # Initialize chat history for this conversation
    if conversation_id not in chat_history:
        chat_history[conversation_id] = []
    
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            
            # Check if this is an end_chat message
            if msg.get("end_chat") == True:
                # Set end time
                conversation_data[conversation_id]["end_time"] = datetime.datetime.now()
                
                # Notify the other participant
                other_role = "agent" if role == "customer" else "customer"
                if other_role in connections:
                    await connections[other_role]["ws"].send_text(json.dumps({
                        "system_message": "Chat has ended",
                        "end_chat": True
                    }))
                
                # Send full chat history to n8n
                if N8N_ENABLED:
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:  # Add timeout
                            # Combine conversation data and chat history
                            payload = {
                                **conversation_data[conversation_id],
                                "event": "chat_ended",
                                "ended_by": role,
                                "chat_history": chat_history[conversation_id],
                            }
                            
                            # Convert datetime objects to ISO format strings
                            payload["start_time"] = payload["start_time"].isoformat()
                            payload["end_time"] = payload["end_time"].isoformat()
                            
                            response = await client.post(N8N_WEBHOOK_URL, json=payload)
                            print(f"n8n webhook response: {response.status_code} - {response.text[:100]}")
                    except Exception as e:
                        print(f"Failed to send to n8n: {str(e)} ({type(e).__name__})")
                
                # Clean up
                if conversation_id in chat_history:
                    del chat_history[conversation_id]
                if conversation_id in conversation_data:
                    del conversation_data[conversation_id]
                break
            
            # Process regular messages
            if "msg" in msg:
                # Update customer language if detected
                if role == "customer" and "lang" in msg:
                    conversation_data[conversation_id]["customer_language"] = msg.get("lang", "en")
                
                translated = translate_text(msg["msg"], msg.get("lang", "en"), 
                                          "ar" if role == "customer" else "en")
                
                # Store message in chat history
                chat_history[conversation_id].append({
                    "role": role,
                    "original": msg["msg"],
                    "translated": translated,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "language": msg.get("lang", "en")
                })
                
                # Send to opposite role
                other_role = "agent" if role == "customer" else "customer"
                if other_role in connections:
                    await connections[other_role]["ws"].send_text(json.dumps({
                        "msg": translated,
                        "original": msg["msg"]
                    }))

    except WebSocketDisconnect:
        # Handle disconnection
        if role in connections:
            del connections[role]
        
        # Treat disconnection as implicit chat ending
        if N8N_ENABLED and conversation_id in conversation_data:
            # Set end time
            conversation_data[conversation_id]["end_time"] = datetime.datetime.now()
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:  # Add timeout
                    # Combine conversation data and chat history
                    payload = {
                        **conversation_data[conversation_id],
                        "event": "chat_disconnected",
                        "disconnected_role": role,
                        "chat_history": chat_history.get(conversation_id, [])
                    }
                    
                    # Convert datetime objects to ISO format strings
                    payload["start_time"] = payload["start_time"].isoformat()
                    payload["end_time"] = payload["end_time"].isoformat()
                    
                    response = await client.post(N8N_WEBHOOK_URL, json=payload)
                    print(f"n8n webhook response: {response.status_code} - {response.text[:100]}")
            except Exception as e:
                print(f"Failed to send to n8n: {str(e)} ({type(e).__name__})")
            
            # Clean up
            if conversation_id in chat_history:
                del chat_history[conversation_id]
            if conversation_id in conversation_data:
                del conversation_data[conversation_id]



