# customer_client.py
import asyncio
import websockets
import json
import sys
import random

async def customer_chat():
    # Generate a random customer ID for this session
    customer_id = f"cust_{random.randint(1000, 9999)}"
    language = "en"
    
    uri = f"ws://localhost:8000/ws/customer?user_id={customer_id}&language={language}"
    
    print(f"Connecting as customer ID: {customer_id}")
    
    async with websockets.connect(uri) as ws:
        # Start message receive task
        receive_task = asyncio.create_task(receive_messages(ws))
        
        try:
            while True:
                # Get user input
                message = input("You (type 'end' to end chat): ")
                
                if message.lower() == "end":
                    # Send end_chat message with optional feedback
                    satisfaction = input("Rate your satisfaction (1-5): ")
                    feedback = input("Any feedback? ")
                    await ws.send(json.dumps({
                        "end_chat": True,
                        "satisfaction": satisfaction,
                        "feedback": feedback
                    }))
                    print("Chat ended.")
                    break
                else:
                    # Send message with language tag
                    await ws.send(json.dumps({"msg": message, "lang": language}))
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
                    print(f"Agent: {data.get('msg', response)}")
            except json.JSONDecodeError:
                print(f"Agent: {response}")
    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")

if __name__ == "__main__":
    asyncio.run(customer_chat())
