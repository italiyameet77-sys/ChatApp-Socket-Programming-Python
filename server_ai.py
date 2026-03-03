# ============================================================
#   CHAT SERVER — DEPLOYMENT LEVEL
#   Features: Multi-client, File Transfer, Private Messaging,
#             Online Users, Message History, Timestamps,
#             SQLite Database, Authentication, SSL Encryption
# ============================================================

import socket
import threading
import os
import ssl
import sqlite3
import bcrypt
from datetime import datetime


# ─────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────

HEADER           = 64
PORT             = 8080
SERVER           = "0.0.0.0"
ADDR             = (SERVER, PORT)
FORMAT           = 'utf-8'
BUFFER           = 1024
HISTORY_LIMIT    = 10
DATABASE_FILE    = "chat.db"
CERT_FILE        = "cert.pem"
KEY_FILE         = "key.pem"

# special command keywords
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_MESSAGE       = "!FILE"
USERS_MESSAGE      = "!USERS"
DM_MESSAGE         = "!DM"
REGISTER_MESSAGE   = "!REGISTER"
LOGIN_MESSAGE      = "!LOGIN"


# ─────────────────────────────────────
# SETUP — FOLDERS
# ─────────────────────────────────────

os.makedirs("server_files", exist_ok=True)


# ─────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────

def init_database():
    """Create database tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sender     TEXT NOT NULL,
            message    TEXT NOT NULL,
            timestamp  TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print(f"[{get_timestamp()}] [DATABASE] Database initialized ✅")


def register_user(username, password):
    """Register a new user. Returns (success, message)."""
    try:
        conn   = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # check if username already exists
        existing = cursor.execute(
            "SELECT username FROM users WHERE username=?", (username,)
        ).fetchone()

        if existing:
            conn.close()
            return False, "Username already taken!"

        # hash the password
        hashed = bcrypt.hashpw(password.encode(FORMAT), bcrypt.gensalt())

        # save to database
        cursor.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, hashed, get_timestamp())
        )
        conn.commit()
        conn.close()
        return True, "Registration successful!"

    except Exception as e:
        return False, f"Registration error: {str(e)}"


def login_user(username, password):
    """Verify login credentials. Returns (success, message)."""
    try:
        conn   = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # find user in database
        user = cursor.execute(
            "SELECT password FROM users WHERE username=?", (username,)
        ).fetchone()

        conn.close()

        if not user:
            return False, "User not found! Please register first."

        # check password against hash
        if bcrypt.checkpw(password.encode(FORMAT), user[0]):
            return True, "Login successful!"
        else:
            return False, "Wrong password!"

    except Exception as e:
        return False, f"Login error: {str(e)}"


def save_message_db(sender, message):
    """Save a message to the database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.execute(
            "INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)",
            (sender, message, get_timestamp())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to save message: {str(e)}")


def get_message_history():
    """Fetch last N messages from database."""
    try:
        conn     = sqlite3.connect(DATABASE_FILE)
        messages = conn.execute(
            "SELECT sender, message, timestamp FROM messages ORDER BY id DESC LIMIT ?",
            (HISTORY_LIMIT,)
        ).fetchall()
        conn.close()
        # reverse to show oldest first
        messages.reverse()
        return messages
    except:
        return []


# ─────────────────────────────────────
# SSL SETUP
# ─────────────────────────────────────

def create_ssl_context():
    """Create SSL context for secure connections."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT_FILE, KEY_FILE)
    print(f"[{get_timestamp()}] [SSL] SSL context created ✅")
    return context


# ─────────────────────────────────────
# SERVER SOCKET SETUP
# ─────────────────────────────────────

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

clients   = []
usernames = []


# ─────────────────────────────────────
# HELPER: TIMESTAMP
# ─────────────────────────────────────

def get_timestamp():
    return datetime.now().strftime("%I:%M %p")


# ─────────────────────────────────────
# CORE: SEND & RECEIVE
# ─────────────────────────────────────

def send_message(conn, msg):
    """Send a message to a specific client with a fixed-size header."""
    try:
        message     = msg.encode(FORMAT)
        msg_length  = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        conn.send(send_length)
        conn.send(message)
    except:
        pass


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
        return None


# ─────────────────────────────────────
# BROADCAST
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
            send_message(client, FILE_MESSAGE)
            send_message(client, filename)
            send_message(client, str(filesize))
            client.send(filedata)


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

    if target_username not in usernames:
        sender_index = usernames.index(sender_username)
        send_message(clients[sender_index], f"[{timestamp}] [ERROR] User '{target_username}' not found!")
        return

    target_index = usernames.index(target_username)
    send_message(clients[target_index], f"[{timestamp}] [PRIVATE] [{sender_username}] {msg}")

    sender_index = usernames.index(sender_username)
    send_message(clients[sender_index], f"[{timestamp}] [PRIVATE → {target_username}] {msg}")


# ─────────────────────────────────────
# MESSAGE HISTORY
# ─────────────────────────────────────

def send_history(conn):
    """Send the last N messages from database to a newly joined client."""
    messages = get_message_history()

    if not messages:
        send_message(conn, "[NO HISTORY YET]")
        return

    send_message(conn, "\n─────── CHAT HISTORY ───────")
    for sender, message, timestamp in messages:
        send_message(conn, f"[{timestamp}] [{sender}] {message}")
    send_message(conn, "─────────── LIVE CHAT ───────────\n")


# ─────────────────────────────────────
# AUTHENTICATION HANDLER
# ─────────────────────────────────────

def authenticate_client(conn):
    """Handle client registration or login. Returns username if successful."""
    while True:
        # receive auth type: !REGISTER or !LOGIN
        auth_type = receive_message(conn)

        if auth_type is None:
            return None

        if auth_type == REGISTER_MESSAGE:
            # receive username and password
            username = receive_message(conn)
            password = receive_message(conn)

            success, message = register_user(username, password)
            send_message(conn, message)

            if success:
                print(f"[{get_timestamp()}] [AUTH] New user registered: {username}")
                return username

        elif auth_type == LOGIN_MESSAGE:
            # receive username and password
            username = receive_message(conn)
            password = receive_message(conn)

            success, message = login_user(username, password)
            send_message(conn, message)

            if success:
                print(f"[{get_timestamp()}] [AUTH] User logged in: {username}")
                return username

        else:
            send_message(conn, "[ERROR] Invalid auth type! Use !REGISTER or !LOGIN")


# ─────────────────────────────────────
# CLIENT HANDLER
# ─────────────────────────────────────

def handle_client(conn, addr):
    print(f"[{get_timestamp()}] [NEW CONNECTION] {addr} connected")

    # authenticate first
    username = authenticate_client(conn)

    if not username:
        conn.close()
        return

    # check if user already connected
    if username in usernames:
        send_message(conn, "[ERROR] This account is already logged in!")
        conn.close()
        return

    usernames.append(username)
    clients.append(conn)
    print(f"[{get_timestamp()}] [AUTHENTICATED] {username} joined from {addr}")

    # send history and announce join
    send_history(conn)
    broadcast(conn, f"[SERVER] {username} joined the chat!")
    save_message_db("SERVER", f"{username} joined the chat!")

    # ── main message loop ──
    connected = True
    while connected:
        msg = receive_message(conn)

        if msg is None:
            connected = False

        elif msg == DISCONNECT_MESSAGE:
            connected = False

        elif msg.startswith(DM_MESSAGE):
            parts = msg.split(" ", 2)
            if len(parts) < 3:
                send_message(conn, f"[{get_timestamp()}] [ERROR] Usage: !DM username message")
            else:
                send_private_message(username, parts[1], parts[2])

        elif msg == USERS_MESSAGE:
            timestamp  = get_timestamp()
            users_list = f"\n[{timestamp}] [ONLINE USERS]\n"
            for i, user in enumerate(usernames, 1):
                users_list += f"  {i}. {user}\n"
            users_list += f"  Total: {len(usernames)} users online"
            send_message(conn, users_list)

        elif msg == FILE_MESSAGE:
            filename, filesize, filedata = receive_file(conn)
            print(f"[{get_timestamp()}] [{username}] sent file: {filename} ({filesize} bytes)")

            with open(f"server_files/server_received_{filename}", 'wb') as f:
                f.write(filedata)

            broadcast_file(filename, filesize, filedata, conn)
            broadcast(conn, f"[{username}] sent a file: {filename}")

        else:
            timestamp = get_timestamp()
            print(f"[{timestamp}] [{username}] {msg}")
            save_message_db(username, msg)
            broadcast(conn, f"[{username}] {msg}")

    # ── cleanup on disconnect ──
    broadcast(conn, f"[SERVER] {username} left the chat!")
    save_message_db("SERVER", f"{username} left the chat!")

    if username in usernames:
        index = usernames.index(username)
        clients.remove(conn)
        usernames.remove(username)

    conn.close()
    print(f"[{get_timestamp()}] [DISCONNECTED] {username} disconnected")


# ─────────────────────────────────────
# START SERVER
# ─────────────────────────────────────

def start():
    # initialize database
    init_database()

    # create SSL context
    ssl_context = create_ssl_context()

    # wrap server with SSL
    secure_server = ssl_context.wrap_socket(server, server_side=True)

    secure_server.listen()
    print(f"[{get_timestamp()}] [LISTENING] Secure server listening on port {PORT} 🔐")

    while True:
        try:
            conn, addr = secure_server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
            print(f"[{get_timestamp()}] [ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        except Exception as e:
            print(f"[ERROR] {str(e)}")


print("[STARTING] Secure server is starting...")
start()