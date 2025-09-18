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

URI = f"ws://13.60.58.231:8000/ws/agent?user_id={st.session_state.agent_id}"

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

# UI: input field and send button
user_input = st.text_input("💬 You:", key="user_input")

if st.button("Send"):
    msg = user_input.strip()
    if msg:
        # Add your own message to history immediately (server doesn't echo back)
        st.session_state.messages.append(f"📤 Sent: {msg}")
        st.session_state.outgoing_queue.put({"msg": msg, "lang": "ar"})
        st.session_state.user_input = ""  # Clear input after sending
        st.rerun()  # Optional: Force immediate refresh to show the message

# Drain incoming queue - add deduplication to prevent repeats
q = st.session_state.incoming_queue
added = False
seen_messages = set()  # Track seen messages to avoid repeats
while not q.empty():
    try:
        sender, msg, original = q.get_nowait()
        message_key = (sender, msg, original)  # Unique key for deduplication
        if message_key not in seen_messages:
            seen_messages.add(message_key)
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
    except Exception:
        break

# --- End Chat Button ---
if st.button("🔴 End Chat"):
    try:
        # Send a signal to server that agent disconnected
        st.session_state.outgoing_queue.put({"end_chat": True})  # Fixed: Send in server-expected format
    except:
        pass
    st.session_state.messages.append("🚪 You ended the chat.")  # Fixed: Use 'messages' (list of strings) instead of 'chat_history'
    st.stop()  # stops Streamlit rerun so thread won't keep running

# Render messages
st.write("---")
for message in st.session_state.messages:
    st.write(message)

# If we consumed messages, request a rerun to show them immediately
if added:
    st.rerun()
