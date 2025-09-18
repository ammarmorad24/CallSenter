import streamlit as st
import asyncio
import websockets
import json
import random

# Function to connect to the WebSocket and handle chat
async def agent_chat(agent_id):
    uri = f"ws://127.0.0.1:8000/ws/agent?user_id={agent_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            # Wait for user input from Streamlit
            user_input = st.session_state.get('user_input')
            if user_input:
                await websocket.send(json.dumps({"msg": user_input, "lang": "ar"}))
                st.session_state['user_input'] = ""  # Clear input after sending

            # Receive messages from the WebSocket
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if "msg" in data:
                    st.session_state['chat_history'].append(f"👤 Customer: {data['msg']}")
                elif "system_message" in data:
                    st.session_state['chat_history'].append(f"🔔 System: {data['system_message']}")
                if data.get("end_chat"):
                    break
            except websockets.exceptions.ConnectionClosed:
                break

# Streamlit application layout
def main():
    st.title("Chat Agent")
    
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'user_input' not in st.session_state:
        st.session_state['user_input'] = ""

    agent_id = f"agent_{random.randint(1000, 9999)}"
    st.write(f"👤 Agent ID: {agent_id}")

    # Display chat history
    for message in st.session_state['chat_history']:
        st.write(message)

    # User input
    user_input = st.text_input("💬 You:", key='user_input')
    
    if st.button("Send"):
        asyncio.run(agent_chat(agent_id))

if __name__ == "__main__":
    main()
