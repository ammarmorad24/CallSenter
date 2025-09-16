# customer_client/main.py - SIMPLIFIED DEBUG VERSION
import asyncio
import websockets
import json
import random

async def customer_chat():
    customer_id = f"cust_{random.randint(1000, 9999)}"
    
    # UPDATE THIS LINE WITH YOUR EC2 IP:
    uri = f"ws://51.20.54.101:8000/ws/customer?user_id={customer_id}"
    # For EC2: uri = f"ws://YOUR-EC2-IP:8000/ws/customer?user_id={customer_id}"
    
    print(f"🌟 Customer Client Starting")
    print(f"👤 Customer ID: {customer_id}")
    print(f"🔗 Connecting to: {uri}")
    
    try:
        async with websockets.connect(
            uri,
            ping_interval=30,  # Send ping every 30 seconds
            ping_timeout=10,   # Wait 10 seconds for pong
            close_timeout=10   # Wait 10 seconds when closing
        ) as websocket:
            print("✅ Connected! Waiting for agent...")
            
            # Start background task to receive messages
            receive_task = asyncio.create_task(receive_messages(websocket))
            
            try:
                while True:
                    # Get user input (this is blocking, but that's OK for testing)
                    message = await asyncio.to_thread(input, "\n💬 You: ")
                    
                    if message.lower() in ['end', 'quit', 'exit']:
                        print("👋 Ending chat...")
                        await websocket.send(json.dumps({"end_chat": True}))
                        break
                    
                    if message.strip():  # Don't send empty messages
                        await websocket.send(json.dumps({
                            "msg": message,
                            "lang": "en"  # Customer speaks English
                        }))
                        print(f"📤 Sent: {message}")
            
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted! Closing...")
                try:
                    await websocket.send(json.dumps({"end_chat": True}))
                except:
                    pass
            finally:
                receive_task.cancel()
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print(f"   Make sure chat service is running on the server!")

async def receive_messages(websocket):
    try:
        while True:
            message = await websocket.recv()
            print(f"\n📨 Raw received: {message}")
            
            try:
                data = json.loads(message)
                
                if "system_message" in data:
                    status = data.get("status", "")
                    print(f"🔔 System: {data['system_message']}")
                    
                    if data.get("end_chat"):
                        break
                        
                elif "msg" in data:
                    translated = data["msg"]
                    original = data.get("original", "")
                    
                    print(f"🧑‍💼 Agent: {translated}")
                    if original and original != translated:
                        print(f"   📝 (Original: {original})")
                else:
                    print(f"🔄 Other message: {data}")
                    
            except json.JSONDecodeError:
                print(f"📨 Agent: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        print("\n🔌 Connection closed")
    except Exception as e:
        print(f"\n❌ Error receiving: {e}")

if __name__ == "__main__":
    asyncio.run(customer_chat())
