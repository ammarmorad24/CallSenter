# streamlit_customer.py (patched)
from streamlit_autorefresh import st_autorefresh
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

st.set_page_config(page_title="Customer Chat", page_icon="🧑")

# -----------------------------
# <-- IMPORTANT: auto-refresh
# rerun every 300 ms for near real-time feel
st_autorefresh(interval=300, key="auto_refresh")
# -----------------------------

# --- Initialize session state BEFORE starting threads ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "customer_id" not in st.session_state:
    st.session_state.customer_id = f"cust_{random.randint(1000, 9999)}"
if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()
if "thread_started" not in st.session_state:
    st.session_state.thread_started = False

# Communication queues
if "incoming_queue" not in st.session_state:
    st.session_state.incoming_queue = queue.Queue()
if "outgoing_queue" not in st.session_state:
    st.session_state.outgoing_queue = queue.Queue()

URI = f"ws://127.0.0.1:8000/ws/customer?user_id={st.session_state.customer_id}&language=en"

st.title(" Customer Client")
st.write(f"**Customer ID:** {st.session_state.customer_id}")
st.write(f"**Server:** {URI}")

# Background coroutine: connects once, then starts sender task and receives messages
async def connect_and_listen(q_in: queue.Queue, q_out: queue.Queue, client_id: str):
    try:
        async with websockets.connect(URI) as ws:
            # Notify main thread
            q_in.put(("system", f"✅ Connected as {client_id}", ""))
            # start sender task
            async def sender_loop():
                while True:
                    try:
                        item = q_out.get_nowait()
                    except Exception:
                        await asyncio.sleep(0.05)
                        continue
                    # expected item = dict with keys 'msg' and 'lang'
                    try:
                        await ws.send(json.dumps(item))
                    except Exception as e:
                        q_in.put(("system", f"❌ Send error: {e}", ""))
            sender_task = asyncio.create_task(sender_loop())

            # receive loop
            while True:
                data = await ws.recv()
                msg = json.loads(data)
                if "system_message" in msg:
                    q_in.put(("system", msg["system_message"], ""))
                elif "msg" in msg:
                    # <-- USE the 'from' field (who sent the message)
                    sender_role = msg.get("from", "agent")
                    q_in.put((sender_role, msg["msg"], msg.get("original", "")))
    except Exception as e:
        q_in.put(("system", f"❌ Connection error: {e}", ""))

def start_background_loop(loop, q_in, q_out, client_id):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_and_listen(q_in, q_out, client_id))

# Start background thread ONCE
if not st.session_state.thread_started:
    thread = threading.Thread(
        target=start_background_loop,
        args=(st.session_state.loop, st.session_state.incoming_queue, st.session_state.outgoing_queue, st.session_state.customer_id),
        daemon=True
    )
    thread.start()
    st.session_state.thread_started = True
    # small pause to let thread begin connecting (optional)
    time.sleep(0.05)

# UI send callback: push into outgoing_queue (background sender will send via same ws)
# def send_and_clear():
#     msg = st.session_state.user_input.strip()
#     if not msg:
#         return
#     st.session_state.chat_history.append(("customer", msg, ""))
#     st.session_state.user_input = ""
#     # enqueue the payload that the server expects
#     st.session_state.outgoing_queue.put({"msg": msg, "lang": "en"})
def send_and_clear():
    msg = st.session_state.user_input.strip()
    if not msg:
        return
    # REMOVE this line (causes duplication):
    # st.session_state.chat_history.append(("customer", msg, ""))
    st.session_state.user_input = ""
    st.session_state.outgoing_queue.put({"msg": msg, "lang": "en"})

st.text_input("💬 You:", key="user_input", on_change=send_and_clear)

# Drain incoming queue (main thread only)
q = st.session_state.incoming_queue
added = False
while not q.empty():
    try:
        sender, msg, original = q.get_nowait()
    except Exception:
        break
    added = True
    if sender == "system":
        st.session_state.chat_history.append(("system", msg, ""))
    elif sender == "agent":
        st.session_state.chat_history.append(("agent", msg, original))
    elif sender == "customer":
        st.session_state.chat_history.append(("customer", msg, original))
    else:
        st.session_state.chat_history.append((sender, msg, original))

# --- End Chat Button ---
if st.button("🔴 End Chat"):
    try:
        # Send a signal to server that customer disconnected
        st.session_state.outgoing_queue.put({"msg": "end_chat"})
    except:
        pass
    st.session_state.chat_history.append(("system", "🚪 You ended the chat.", ""))
    st.stop()  # stops Streamlit rerun so thread won't keep running


# Render chat
st.write("---")
for sender, msg, original in st.session_state.chat_history:
    if sender == "customer":
        st.markdown(f"**You:** {msg}")
    elif sender == "agent":
        st.markdown(f"**Agent:** {msg}")
        if original and original != msg:
            st.markdown(f"<span style='font-size:small;'>(Original: {original})</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"*{msg}*")

# If new messages were added this run, refresh to show them immediately
if added:
    st.rerun()
