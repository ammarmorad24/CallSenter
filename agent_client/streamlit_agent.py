from streamlit_autorefresh import st_autorefresh

# rerun every 1000 ms (1 second). Lower interval = faster updates (higher CPU).
st_autorefresh(interval=300, key="auto_refresh")

import streamlit as st
import asyncio
import websockets
import json
import random
import threading
import queue
import sys, os
import time

# Add project root (CallSenter) to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from chat_service.translate import translate_en_to_ar, translate_ar_to_en

st.set_page_config(page_title="Agent Chat", page_icon="💬")

# --- Initialize session state BEFORE starting threads ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_id" not in st.session_state:
    st.session_state.agent_id = f"agent_{random.randint(1000, 9999)}"
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
if "thread_started" not in st.session_state:
    st.session_state.thread_started = False

# Queues
if "incoming_queue" not in st.session_state:
    st.session_state.incoming_queue = queue.Queue()
if "outgoing_queue" not in st.session_state:
    st.session_state.outgoing_queue = queue.Queue()

URI = f"ws://127.0.0.1:8000/ws/agent?user_id={st.session_state.agent_id}"

st.title(" Agent Client ")
st.write(f"**Agent ID:** {st.session_state.agent_id}")
st.write(f"**Server:** {URI}")

# Background coroutine: connect once, spawn sender_loop, receive messages and push to incoming_queue
async def connect_and_listen(q_in: queue.Queue, q_out: queue.Queue, agent_id: str):
    try:
        async with websockets.connect(URI) as ws:
            q_in.put(("system", "✅ Connected to chat service.", ""))
            async def sender_loop():
                while True:
                    try:
                        item = q_out.get_nowait()
                    except Exception:
                        await asyncio.sleep(0.05)
                        continue
                    try:
                        await ws.send(json.dumps(item))
                    except Exception as e:
                        q_in.put(("system", f"❌ Send error: {e}", ""))
            sender_task = asyncio.create_task(sender_loop())

            while True:
                data = await ws.recv()
                msg = json.loads(data)
                if "system_message" in msg:
                    q_in.put(("system", msg["system_message"], ""))
                elif "msg" in msg:
                    q_in.put(("agent", msg["msg"], msg.get("original", "")))
    except Exception as e:
        q_in.put(("system", f"❌ Connection error: {e}", ""))

def start_background_loop(loop, q_in, q_out, agent_id):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_and_listen(q_in, q_out, agent_id))

# Start background thread ONCE
if not st.session_state.thread_started:
    thread = threading.Thread(
        target=start_background_loop,
        args=(st.session_state.loop, st.session_state.incoming_queue, st.session_state.outgoing_queue, st.session_state.agent_id),
        daemon=True
    )
    thread.start()
    st.session_state.thread_started = True
    time.sleep(0.05)

# UI send: enqueue on outgoing_queue
# def send_and_clear():
#     msg = st.session_state.user_input.strip()
#     if not msg:
#         return
#     st.session_state.messages.append(f"📤 Sent: {msg}")
#     st.session_state.user_input = ""
#     st.session_state.outgoing_queue.put({"msg": msg, "lang": "ar"})
def send_and_clear():
    msg = st.session_state.user_input.strip()
    if not msg:
        return
    # REMOVE this line (causes duplication):
    # st.session_state.messages.append(f"📤 Sent: {msg}")
    st.session_state.user_input = ""
    st.session_state.outgoing_queue.put({"msg": msg, "lang": "ar"})

st.text_input("💬 You:", key="user_input", on_change=send_and_clear)

# Drain incoming queue
q = st.session_state.incoming_queue
added = False
while not q.empty():
    try:
        sender, msg, original = q.get_nowait()
    except Exception:
        break
    added = True
    if sender == "system":
        st.session_state.messages.append(f"*{msg}*")
    elif sender == "agent":
        display = f"👤 Customer: {msg}"
        if original and original != msg:
            display += f"\n   📝 (Original: {original})"
        st.session_state.messages.append(display)
    else:
        st.session_state.messages.append(str((sender, msg, original)))


# --- End Chat Button ---
if st.button("🔴 End Chat"):
    try:
        # Send a signal to server that customer disconnected
        st.session_state.outgoing_queue.put({"msg": "end_chat"})
    except:
        pass
    st.session_state.chat_history.append(("system", "🚪 You ended the chat.", ""))
    st.stop()  # stops Streamlit rerun so thread won't keep running


# Render messages
st.write("---")
for message in st.session_state.messages:
    st.write(message)

# If we consumed messages, request a rerun to show them immediately
if added:
    st.rerun()


# import streamlit as st
# import asyncio
# import websockets
# import json
# import random

# st.set_page_config(page_title="Agent Chat", page_icon="💬")

# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "agent_id" not in st.session_state:
#     st.session_state.agent_id = f"agent_{random.randint(1000, 9999)}"
# if "connected" not in st.session_state:
#     st.session_state.connected = False
# if "user_input" not in st.session_state:
#     st.session_state.user_input = ""

# uri = f"ws://127.0.0.1:8000/ws/agent?user_id={st.session_state.agent_id}"

# st.title("🌟 Agent Client (Streamlit)")
# st.write(f"**Agent ID:** {st.session_state.agent_id}")
# st.write(f"**Server:** {uri}")

# async def send_message(msg):
#     try:
#         async with websockets.connect(uri) as websocket:
#             await websocket.send(json.dumps({"msg": msg, "lang": "ar"}))
#             response = await websocket.recv()
#             data = json.loads(response)
#             if "system_message" in data:
#                 st.session_state.messages.append(f"🔔 System: {data['system_message']}")
#             elif "msg" in data:
#                 translated = data["msg"]
#                 original = data.get("original", "")
#                 msg = f"👤 Customer: {translated}"
#                 if original and original != translated:
#                     msg += f"\n   📝 (Original: {original})"
#                 st.session_state.messages.append(msg)
#             else:
#                 st.session_state.messages.append(f"🔄 Other message: {data}")
#     except Exception as e:
#         st.session_state.messages.append(f"❌ Connection error: {e}")

# # callback function to send & clear
# def send_and_clear():
#     if st.session_state.user_input.strip():
#         asyncio.run(send_message(st.session_state.user_input))
#         st.session_state.messages.append(f"📤 Sent: {st.session_state.user_input}")
#         st.session_state.user_input = ""  # clear input

# st.text_input("💬 You:", key="user_input", on_change=send_and_clear)

# if st.button("Refresh"):
#     async def receive_message():
#         try:
#             async with websockets.connect(uri) as websocket:
#                 response = await websocket.recv()
#                 data = json.loads(response)
#                 if "system_message" in data:
#                     st.session_state.messages.append(f"🔔 System: {data['system_message']}")
#                 elif "msg" in data:
#                     translated = data["msg"]
#                     original = data.get("original", "")
#                     msg = f"👤 Customer: {translated}"
#                     if original and original != translated:
#                         msg += f"\n   📝 (Original: {original})"
#                     st.session_state.messages.append(msg)
#                 else:
#                     st.session_state.messages.append(f"🔄 Other message: {data}")
#         except Exception as e:
#             st.session_state.messages.append(f"❌ Connection error: {e}")
#     asyncio.run(receive_message())

# st.write("---")
# for msg in st.session_state.messages:
#     st.write(msg)
