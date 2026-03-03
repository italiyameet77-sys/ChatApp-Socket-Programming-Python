# ============================================================
#   CHAT SERVER
#   Features: Multi-client, File Transfer, Private Messaging,
#             Online Users, Message History, Timestamps
# ============================================================

import socket
import threading
import os
from datetime import datetime


# ─────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────

HEADER           = 64                  # fixed header size in bytes
PORT             = 8080                # server port
SERVER           = "0.0.0.0"          # listen on all interfaces
ADDR             = (SERVER, PORT)
FORMAT           = 'utf-8'             # encoding format
BUFFER           = 1024               # file transfer chunk size
HISTORY_FILE     = "chat_history.txt" # chat log file
HISTORY_LIMIT    = 10                 # number of past messages to show on join

# special command keywords
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_MESSAGE       = "!FILE"
USERS_MESSAGE      = "!USERS"
DM_MESSAGE         = "!DM"


# ─────────────────────────────────────
# SETUP
# ─────────────────────────────────────

os.makedirs("server_files", exist_ok=True)  # folder to save received files

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

clients   = []  # list of all connected client sockets
usernames = []  # list of all connected usernames (parallel to clients)


# ─────────────────────────────────────
# HELPER: TIMESTAMP
# ─────────────────────────────────────

def get_timestamp():
    return datetime.now().strftime("%I:%M %p")


# ─────────────────────────────────────
# CORE: SEND & RECEIVE MESSAGES
# ─────────────────────────────────────

def send_message(conn, msg):
    """Send a message to a specific client with a fixed-size header."""
    message     = msg.encode(FORMAT)
    msg_length  = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))  # pad header to fixed size
    conn.send(send_length)
    conn.send(message)


def receive_message(conn):
    """Receive a message from a client. Returns None if connection is lost."""
    try:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            return msg
        return None
    except:
        return None  # client disconnected abruptly


# ─────────────────────────────────────
# BROADCAST: TEXT & FILES
# ─────────────────────────────────────

def broadcast(conn, msg):
    """Send a timestamped message to all clients except the sender."""
    timestamped_msg = f"[{get_timestamp()}] {msg}"
    for client in clients:
        if client != conn:
            send_message(client, timestamped_msg)


def broadcast_file(filename, filesize, filedata, conn):
    """Send a file to all clients except the sender."""
    for client in clients:
        if client != conn:
            send_message(client, FILE_MESSAGE)       # signal: file coming
            send_message(client, filename)            # send filename
            send_message(client, str(filesize))       # send filesize
            client.send(filedata)                     # send raw file bytes


# ─────────────────────────────────────
# FILE TRANSFER
# ─────────────────────────────────────

def receive_file(conn):
    """Receive a file from a client in chunks."""
    filename = receive_message(conn)
    filesize = int(receive_message(conn))

    filedata = b''
    while len(filedata) < filesize:
        chunk = conn.recv(BUFFER)
        if not chunk:
            break
        filedata += chunk

    return filename, filesize, filedata


# ─────────────────────────────────────
# PRIVATE MESSAGING
# ─────────────────────────────────────

def send_private_message(sender_username, target_username, msg):
    """Send a private message from one user to another."""
    timestamp = get_timestamp()

    # check if target user is online
    if target_username not in usernames:
        sender_index = usernames.index(sender_username)
        send_message(clients[sender_index], f"[{timestamp}] [ERROR] User '{target_username}' not found!")
        return

    # send to target
    target_index = usernames.index(target_username)
    send_message(clients[target_index], f"[{timestamp}] [PRIVATE] [{sender_username}] {msg}")

    # confirm to sender
    sender_index = usernames.index(sender_username)
    send_message(clients[sender_index], f"[{timestamp}] [PRIVATE → {target_username}] {msg}")


# ─────────────────────────────────────
# MESSAGE HISTORY
# ─────────────────────────────────────

def save_message(msg):
    """Append a message to the chat history file."""
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + "\n")


def send_history(conn):
    """Send the last N messages from history to a newly joined client."""
    if not os.path.exists(HISTORY_FILE):
        send_message(conn, "[NO HISTORY YET]")
        return

    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    last_messages = lines[-HISTORY_LIMIT:]

    send_message(conn, "\n─────── CHAT HISTORY ───────")
    for line in last_messages:
        send_message(conn, line.strip())
    send_message(conn, "─────────── LIVE CHAT ───────────\n")


# ─────────────────────────────────────
# CLIENT HANDLER (runs on separate thread per client)
# ─────────────────────────────────────

def handle_client(conn, addr):
    # receive username (first message from client)
    username = conn.recv(1024).decode(FORMAT)
    usernames.append(username)
    clients.append(conn)
    print(f"[{get_timestamp()}] [NEW CONNECTION] {username} connected from {addr}")

    # send chat history to new client
    send_history(conn)

    # log and announce join
    join_msg = f"[{get_timestamp()}] [SERVER] {username} joined the chat!"
    save_message(join_msg)
    broadcast(conn, f"[SERVER] {username} joined the chat!")

    # ── main message loop ──
    connected = True
    while connected:
        msg = receive_message(conn)

        if msg is None:
            # client disconnected abruptly
            connected = False

        elif msg == DISCONNECT_MESSAGE:
            connected = False

        elif msg.startswith(DM_MESSAGE):
            # format: !DM <username> <message>
            parts = msg.split(" ", 2)
            if len(parts) < 3:
                send_message(conn, f"[{get_timestamp()}] [ERROR] Usage: !DM username message")
            else:
                send_private_message(username, parts[1], parts[2])

        elif msg == USERS_MESSAGE:
            # build and send online users list
            timestamp  = get_timestamp()
            users_list = f"\n[{timestamp}] [ONLINE USERS]\n"
            for i, user in enumerate(usernames, 1):
                users_list += f"  {i}. {user}\n"
            users_list += f"  Total: {len(usernames)} users online"
            send_message(conn, users_list)

        elif msg == FILE_MESSAGE:
            # receive and forward file
            filename, filesize, filedata = receive_file(conn)
            print(f"[{get_timestamp()}] [{username}] sent file: {filename} ({filesize} bytes)")

            # save on server
            with open(f"server_files/server_received_{filename}", 'wb') as f:
                f.write(filedata)

            broadcast_file(filename, filesize, filedata, conn)
            broadcast(conn, f"[{username}] sent a file: {filename}")

        else:
            # regular message — log, save, broadcast
            timestamp = get_timestamp()
            print(f"[{timestamp}] [{username}] {msg}")
            save_message(f"[{timestamp}] [{username}] {msg}")
            broadcast(conn, f"[{username}] {msg}")

    # ── cleanup on disconnect ──
    broadcast(conn, f"[SERVER] {username} left the chat!")
    save_message(f"[{get_timestamp()}] [SERVER] {username} left the chat!")

    index = clients.index(conn)
    clients.remove(conn)
    usernames.remove(username)
    conn.close()
    print(f"[{get_timestamp()}] [DISCONNECTED] {username} disconnected")


# ─────────────────────────────────────
# START SERVER
# ─────────────────────────────────────

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on port {PORT}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


print("[STARTING] Server is running...")
start()