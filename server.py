import socket
import threading
import os
from datetime import datetime 

HEADER = 64
PORT = 8080
SERVER = "192.168.1.7"
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_MESSAGE = "!FILE"
BUFFER = 1024
USERS_MESSAGE = "!USERS"
DM_MESSAGE = "!DM"
HISTORY_FILE = "chat_history.txt"
HISTORY_LIMIT = 10  # show last 10 messages

os.makedirs("server_files", exist_ok=True)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

clients = []      # list of all connected clients
usernames = []    # list of all usernames


def receive_message(conn):
    try:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            return msg
        return None
    except:
        return None
 

def send_message(conn, msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)  


def broadcast(conn, msg):
    timestamp = datetime.now().strftime("%I:%M %p")
    timestamped_msg = f"[{timestamp}] {msg}"
    # Send message to ALL other connected clients
    for client in clients:
        if client != conn:
            send_message(client, timestamped_msg)


def broadcast_file(filename, filesize, filedata, conn):
    for client in clients:
        if client != conn:
            # Telling receiver a file is coming
            send_message(client, FILE_MESSAGE)
            # Sending filename
            send_message(client, filename)
            # Sending filesize
            send_message(client, str(filesize))
            # Sending actual file data
            client.send(filedata)


def receive_file(conn):
    # Receive filename
    filename = receive_message(conn)
    # Receive filesize
    filesize = int(receive_message(conn))
    
    # Receive file data in chunks
    filedata = b''
    
    while len(filedata) < filesize:
        chunk = conn.recv(BUFFER)
        if not chunk:
            break
        filedata += chunk
    
    return filename, filesize, filedata


def send_private_message(sender_username, target_username, msg):
    timestamp = datetime.now().strftime("%I:%M %p")
    
    # Check if target user exists
    if target_username not in usernames:
        # Send error back to sender
        index = usernames.index(sender_username)
        sender_conn = clients[index]
        send_message(sender_conn, f"[{timestamp}] [ERROR] User '{target_username}' not found!")
        return
    
    # Find target's socket
    index = usernames.index(target_username)
    target_conn = clients[index]
    
    # Send private message to target
    send_message(target_conn, f"[{timestamp}] [PRIVATE] [{sender_username}] {msg}")
    
    # Confirm to sender
    index = usernames.index(sender_username)
    sender_conn = clients[index]
    send_message(sender_conn, f"[{timestamp}] [PRIVATE → {target_username}] {msg}")
    
  
def save_message(msg):
    # Append message to history file
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + "\n")
        
        
def send_history(conn):
    # Check if history file exists
    if not os.path.exists(HISTORY_FILE):
        send_message(conn, "[NO HISTORY YET]")
        return
    
    # Read all lines
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Get last 10 messages
    last_messages = lines[-HISTORY_LIMIT:]
    
    # Send history to new client
    send_message(conn, "\n─────── CHAT HISTORY ───────")
    for line in last_messages:
        send_message(conn, line.strip())
    send_message(conn, "─────── LIVE CHAT ───────\n")
    
    
def handle_client(conn, addr):
    # First message is always username
    username = conn.recv(1024).decode(FORMAT)
    usernames.append(username)
    clients.append(conn)
    
    timestamp = datetime.now().strftime("%I:%M %p")
    print(f"[{timestamp}] [NEW CONNECTION] {username} connected from {addr}")

    # Send history to new client first
    send_history(conn)
    
    # When user joins
    join_msg = f"[{datetime.now().strftime('%I:%M %p')}] [SERVER] {username} joined the chat!"
    save_message(join_msg)
    
    # then Notify everyone that new user joined
    broadcast(conn, f"[SERVER] {username} joined the chat!")
    
    
    connected = True
    while connected:
        msg = receive_message(conn)
        if msg:
            if msg == DISCONNECT_MESSAGE:
                connected = False
            
            elif msg.startswith(DM_MESSAGE):
                # Format: !DM username message
                parts = msg.split(" ", 2)
                if len(parts) < 3:
                    timestamp = datetime.now().strftime("%I:%M %p")
                    send_message(conn, f"[{timestamp}] [ERROR] Usage: !DM username message")
                else:
                    target_username = parts[1]
                    private_msg = parts[2]
                    send_private_message(username, target_username, private_msg)
        
            elif msg == USERS_MESSAGE:
                # Building online users list
                timestamp = datetime.now().strftime("%I:%M %p")
                users_list = f"\n[{timestamp}] [ONLINE USERS]\n"
                for i, user in enumerate(usernames, 1):
                    users_list += f"{i}. {user}\n"
                users_list += f"Total: {len(usernames)} users online"
    
                # Sending list back to requesting client only
                send_message(conn, users_list)
                
            elif msg == FILE_MESSAGE:
                # File is coming
                filename, filesize, filedata = receive_file(conn)
                print(f"[{username}] sent file: {filename} ({filesize} bytes)")
                
                # Save file on server
                with open(f"server_files/server_received_{filename}", 'wb') as f:
                    f.write(filedata)
                
                # Broadcast file to all other clients
                broadcast_file(filename, filesize, filedata, conn)
                broadcast(conn, f"[{username}] sent a file: {filename}")
                
            else:
                timestamp = datetime.now().strftime("%I:%M %p")
                print(f"[{timestamp}] [{username}] {msg}")
                
                # Save message to history
                timestamped_msg = f"[{timestamp}] [{username}] {msg}"
                save_message(timestamped_msg)

                # Broadcast to everyone
                broadcast(conn, f"[{username}] {msg}")
    
    
    # Notify everyone that user left
    broadcast(conn, f"[SERVER] {username} left the chat!")
    
    # When user leaves
    leave_msg = f"[{datetime.now().strftime('%I:%M %p')}] [SERVER] {username} left the chat!"
    save_message(leave_msg)
        
    # Remove client when disconnected
    index = clients.index(conn)
    clients.remove(conn)
    usernames.remove(username)
    conn.close()
    timestamp = datetime.now().strftime("%I:%M %p")
    print(f"[{timestamp}] [DISCONNECTED] {username} disconnected")
        
        
def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] server is running...")
start()