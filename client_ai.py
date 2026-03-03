# ============================================================
#   CHAT CLIENT — DEPLOYMENT LEVEL
#   Commands:
#     !DISCONNECT        → leave the chat
#     !USERS             → see online users
#     !DM <user> <msg>   → private message
#     !SENDFILE <path>   → send a file
# ============================================================

import socket
import threading
import os
import ssl
from datetime import datetime


# ─────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────

HEADER   = 64
PORT     = 8080
FORMAT   = 'utf-8'
BUFFER   = 1024
SERVER   = "192.168.1.7"   # change to server's IP
ADDR     = (SERVER, PORT)
CERT_FILE = "cert.pem"     # must be same cert as server

# special command keywords
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_MESSAGE       = "!FILE"
USERS_MESSAGE      = "!USERS"
DM_MESSAGE         = "!DM"
REGISTER_MESSAGE   = "!REGISTER"
LOGIN_MESSAGE      = "!LOGIN"


# ─────────────────────────────────────
# SETUP
# ─────────────────────────────────────

os.makedirs("received_files", exist_ok=True)


# ─────────────────────────────────────
# HELPER: TIMESTAMP
# ─────────────────────────────────────

def get_timestamp():
    return datetime.now().strftime("%I:%M %p")


# ─────────────────────────────────────
# SSL SETUP
# ─────────────────────────────────────

def create_ssl_context():
    """Create SSL context for secure connection to server."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(CERT_FILE)  # verify server's certificate
    context.check_hostname = False            # disable hostname check for self-signed cert
    return context


# ─────────────────────────────────────
# CORE: SEND MESSAGE
# ─────────────────────────────────────

def send(msg):
    """Send a text message to the server with a fixed-size header."""
    try:
        message     = msg.encode(FORMAT)
        msg_length  = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)
    except:
        print("[ERROR] Failed to send message!")


# ─────────────────────────────────────
# FILE TRANSFER: SEND
# ─────────────────────────────────────

def send_file(filepath):
    """Read a file and send it to the server."""
    if not os.path.exists(filepath):
        print("[ERROR] File not found!")
        return

    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)

    with open(filepath, 'rb') as f:
        filedata = f.read()

    send(FILE_MESSAGE)
    send(filename)
    send(str(filesize))
    client.send(filedata)

    print(f"[{get_timestamp()}] [SENT] {filename} ({filesize} bytes)")


# ─────────────────────────────────────
# FILE TRANSFER: RECEIVE
# ─────────────────────────────────────

def receive_file():
    """Receive a file from the server in chunks and save it."""
    msg_length = client.recv(HEADER).decode(FORMAT)
    filename   = client.recv(int(msg_length)).decode(FORMAT)

    msg_length = client.recv(HEADER).decode(FORMAT)
    filesize   = int(client.recv(int(msg_length)).decode(FORMAT))

    filedata = b''
    while len(filedata) < filesize:
        chunk = client.recv(BUFFER)
        if not chunk:
            break
        filedata += chunk

    with open(f"received_files/received_{filename}", 'wb') as f:
        f.write(filedata)

    print(f"[{get_timestamp()}] [RECEIVED] File saved as: received_{filename}")


# ─────────────────────────────────────
# RECEIVE THREAD
# ─────────────────────────────────────

def receive():
    """Continuously listen for incoming messages from the server."""
    while True:
        try:
            msg_length = client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(FORMAT)

                if msg == FILE_MESSAGE:
                    receive_file()
                else:
                    print(msg)
        except:
            print("[DISCONNECTED] Lost connection to server")
            break


# ─────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────

def authenticate():
    """Handle registration or login."""
    print("\n" + "="*40)
    print("       WELCOME TO CHAT APP 🔐")
    print("="*40)
    print("1. Login")
    print("2. Register")
    print("="*40)

    while True:
        choice = input("Enter choice (1 or 2): ").strip()

        if choice == "1":
            # login
            username = input("Username: ").strip()
            password = input("Password: ").strip()

            send(LOGIN_MESSAGE)
            send(username)
            send(password)

            # wait for server response
            msg_length = client.recv(HEADER).decode(FORMAT)
            response   = client.recv(int(msg_length)).decode(FORMAT)
            print(f"\n[SERVER] {response}")

            if "successful" in response.lower():
                return username
            else:
                print("Try again!\n")

        elif choice == "2":
            # register
            username = input("Choose username: ").strip()
            password = input("Choose password: ").strip()

            send(REGISTER_MESSAGE)
            send(username)
            send(password)

            # wait for server response
            msg_length = client.recv(HEADER).decode(FORMAT)
            response   = client.recv(int(msg_length)).decode(FORMAT)
            print(f"\n[SERVER] {response}")

            if "successful" in response.lower():
                return username
            else:
                print("Try again!\n")

        else:
            print("Invalid choice! Enter 1 or 2")


# ─────────────────────────────────────
# MAIN: CONNECT & START
# ─────────────────────────────────────

# create SSL context
ssl_context = create_ssl_context()

# create socket
raw_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# wrap with SSL
client = ssl_context.wrap_socket(raw_client, server_hostname=SERVER)

# connect to server
try:
    client.connect(ADDR)
    print(f"[{get_timestamp()}] [CONNECTED] Secure connection established 🔐")
except Exception as e:
    print(f"[ERROR] Could not connect to server: {str(e)}")
    exit()

# authenticate
username = authenticate()

# start receive thread
receive_thread = threading.Thread(target=receive)
receive_thread.daemon = True
receive_thread.start()

print(f"\n[{get_timestamp()}] Welcome {username}! Type !DISCONNECT to leave.\n")


# ─────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────

while True:
    msg = input()

    if msg == DISCONNECT_MESSAGE:
        send(DISCONNECT_MESSAGE)
        print(f"[{get_timestamp()}] You left the chat.")
        break

    elif msg.startswith(DM_MESSAGE):
        parts = msg.split(" ", 2)
        if len(parts) < 3:
            print("[ERROR] Usage: !DM username message")
        else:
            send(msg)

    elif msg == USERS_MESSAGE:
        send(USERS_MESSAGE)

    elif msg.startswith("!SENDFILE"):
        parts = msg.split(" ", 1)
        if len(parts) < 2:
            print("[ERROR] Usage: !SENDFILE filepath")
        else:
            send_file(parts[1])

    else:
        send(msg)
        print(f"[{get_timestamp()}] [YOU] {msg}")