# agent_client.py
import asyncio
import websockets
import json
import random

async def agent_chat():
    # Generate a random agent ID for this session
    agent_id = f"agent_{random.randint(1000, 9999)}"
    
    uri = f"ws://localhost:8000/ws/agent?user_id={agent_id}"
    
    print(f"Connecting as agent ID: {agent_id}")
    
    async with websockets.connect(uri) as ws:
        # Start message receive task
        receive_task = asyncio.create_task(receive_messages(ws))
        
        try:
            while True:
                # Get agent input
                message = input("You (type 'end' to end chat): ")
                
                if message.lower() == "end":
                    # Send end_chat message
                    await ws.send(json.dumps({
                        "end_chat": True
                    }))
                    print("Chat ended.")
                    break
                else:
                    # Send regular message
                    await ws.send(json.dumps({"msg": message, "lang": "ar"}))
                    print(f"You: {message}")
        
        except KeyboardInterrupt:
            print("Closing connection...")
        finally:
            receive_task.cancel()

async def receive_messages(ws):
    try:
        while True:
            response = await ws.recv()
            try:
                data = json.loads(response)
                if data.get("end_chat") == True:
                    print(f"System: {data.get('system_message', 'Chat ended')}")
                    break
                else:
                    print(f"Customer: {data.get('msg', response)}")
            except json.JSONDecodeError:
                print(f"Customer: {response}")
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")

if __name__ == "__main__":
    asyncio.run(agent_chat())
