# ============================================================
#   CHAT CLIENT
#   Commands:
#     !DISCONNECT        → leave the chat
#     !USERS             → see online users
#     !DM <user> <msg>   → private message
#     !SENDFILE <path>   → send a file
# ============================================================

import socket
import threading
import os
from datetime import datetime


# ─────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────

HEADER   = 64               # fixed header size in bytes
PORT     = 8080             # server port
FORMAT   = 'utf-8'          # encoding format
BUFFER   = 1024             # file transfer chunk size
SERVER   = "192.168.1.7"   # server's IP address (change to server's actual IP)
ADDR     = (SERVER, PORT)

# special command keywords
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_MESSAGE       = "!FILE"
USERS_MESSAGE      = "!USERS"
DM_MESSAGE         = "!DM"


# ─────────────────────────────────────
# SETUP
# ─────────────────────────────────────

os.makedirs("received_files", exist_ok=True)  # folder to save received files

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


# ─────────────────────────────────────
# HELPER: TIMESTAMP
# ─────────────────────────────────────

def get_timestamp():
    return datetime.now().strftime("%I:%M %p")


# ─────────────────────────────────────
# CORE: SEND MESSAGE
# ─────────────────────────────────────

def send(msg):
    """Send a text message to the server with a fixed-size header."""
    message     = msg.encode(FORMAT)
    msg_length  = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))  # pad header to fixed size
    client.send(send_length)
    client.send(message)


# ─────────────────────────────────────
# FILE TRANSFER: SEND
# ─────────────────────────────────────

def send_file(filepath):
    """Read a file and send it to the server."""
    if not os.path.exists(filepath):
        print("[ERROR] File not found!")
        return

    filename = os.path.basename(filepath)  # extract filename from full path
    filesize = os.path.getsize(filepath)   # get file size in bytes

    with open(filepath, 'rb') as f:
        filedata = f.read()

    send(FILE_MESSAGE)       # signal: file is coming
    send(filename)            # send filename
    send(str(filesize))       # send filesize
    client.send(filedata)     # send raw file bytes

    print(f"[{get_timestamp()}] [SENT] {filename} ({filesize} bytes)")


# ─────────────────────────────────────
# FILE TRANSFER: RECEIVE
# ─────────────────────────────────────

def receive_file():
    """Receive a file from the server in chunks and save it."""
    # receive filename
    msg_length = client.recv(HEADER).decode(FORMAT)
    filename   = client.recv(int(msg_length)).decode(FORMAT)

    # receive filesize
    msg_length = client.recv(HEADER).decode(FORMAT)
    filesize   = int(client.recv(int(msg_length)).decode(FORMAT))

    # receive file data in chunks
    filedata = b''
    while len(filedata) < filesize:
        chunk = client.recv(BUFFER)
        if not chunk:
            break
        filedata += chunk

    # save received file
    with open(f"received_files/received_{filename}", 'wb') as f:
        f.write(filedata)

    print(f"[{get_timestamp()}] [RECEIVED] File saved as: received_{filename}")


# ─────────────────────────────────────
# RECEIVE THREAD (runs in background)
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
                    receive_file()  # handle incoming file
                else:
                    print(msg)      # print regular message

        except:
            print("[DISCONNECTED] Lost connection to server")
            break


# ─────────────────────────────────────
# MAIN: LOGIN & START
# ─────────────────────────────────────

# send username to server first
username = input("Enter your username: ")
client.send(username.encode(FORMAT))

# start background thread to receive messages
receive_thread = threading.Thread(target=receive)
receive_thread.daemon = True  # thread dies automatically when main program exits
receive_thread.start()

print(f"[{get_timestamp()}] Connected as {username}. Type !DISCONNECT to leave.\n")


# ─────────────────────────────────────
# MAIN LOOP: HANDLE USER INPUT
# ─────────────────────────────────────

while True:
    msg = input()

    if msg == DISCONNECT_MESSAGE:
        # leave the chat
        send(DISCONNECT_MESSAGE)
        print(f"[{get_timestamp()}] You left the chat.")
        break

    elif msg.startswith(DM_MESSAGE):
        # private message → format: !DM <username> <message>
        parts = msg.split(" ", 2)
        if len(parts) < 3:
            print("[ERROR] Usage: !DM username message")
        else:
            send(msg)

    elif msg == USERS_MESSAGE:
        # request online users list
        send(USERS_MESSAGE)

    elif msg.startswith("!SENDFILE"):
        # send a file → format: !SENDFILE <filepath>
        parts = msg.split(" ", 1)
        if len(parts) < 2:
            print("[ERROR] Usage: !SENDFILE filepath")
        else:
            send_file(parts[1])

    else:
        # regular message
        send(msg)
        print(f"[{get_timestamp()}] [YOU] {msg}")  # show own message with timestamp