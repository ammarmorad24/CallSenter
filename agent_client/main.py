import streamlit as st
import asyncio
import websockets
import json
import random

st.set_page_config(page_title="Agent Chat", page_icon="💬")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_id" not in st.session_state:
    st.session_state.agent_id = f"agent_{random.randint(1000, 9999)}"
if "connected" not in st.session_state:
    st.session_state.connected = False
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

uri = f"ws://51.20.54.101:8000/ws/agent?user_id={st.session_state.agent_id}"

st.title("🌟 Agent Client (Streamlit)")
st.write(f"**Agent ID:** {st.session_state.agent_id}")
st.write(f"**Server:** {uri}")

async def send_message(msg):
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"msg": msg, "lang": "ar"}))
            response = await websocket.recv()
            data = json.loads(response)
            if "system_message" in data:
                st.session_state.messages.append(f"🔔 System: {data['system_message']}")
            elif "msg" in data:
                translated = data["msg"]
                original = data.get("original", "")
                msg = f"👤 Customer: {translated}"
                if original and original != translated:
                    msg += f"\n   📝 (Original: {original})"
                st.session_state.messages.append(msg)
            else:
                st.session_state.messages.append(f"🔄 Other message: {data}")
    except Exception as e:
        st.session_state.messages.append(f"❌ Connection error: {e}")

# callback function to send & clear
def send_and_clear():
    if st.session_state.user_input.strip():
        asyncio.run(send_message(st.session_state.user_input))
        st.session_state.messages.append(f"📤 Sent: {st.session_state.user_input}")
        # هنا نمسح الـ input في نفس callback
        st.session_state.user_input = ""  # مسموح هنا لأننا جوه callback

# widget with callback
st.text_input("💬 You:", key="user_input", on_change=send_and_clear)

# زرار Refresh
if st.button("Refresh"):
    async def receive_message():
        try:
            async with websockets.connect(uri) as websocket:
                response = await websocket.recv()
                data = json.loads(response)
                if "system_message" in data:
                    st.session_state.messages.append(f"🔔 System: {data['system_message']}")
                elif "msg" in data:
                    translated = data["msg"]
                    original = data.get("original", "")
                    msg = f"👤 Customer: {translated}"
                    if original and original != translated:
                        msg += f"\n   📝 (Original: {original})"
                    st.session_state.messages.append(msg)
                else:
                    st.session_state.messages.append(f"🔄 Other message: {data}")
        except Exception as e:
            st.session_state.messages.append(f"❌ Connection error: {e}")
    asyncio.run(receive_message())

st.write("---")
for msg in st.session_state.messages:
    st.write(msg)
