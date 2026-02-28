import socket
import threading
import os

HEADER = 64
PORT = 8080
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_MESSAGE = "!FILE"
SERVER = "192.168.31.248"
ADDR = (SERVER, PORT)
BUFFER = 1024

os.makedirs("received_files", exist_ok=True)


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    

def send_file(filepath):
    # Check if file exists
    if not os.path.exists(filepath):
        print("[ERROR] File not found!")
        return
    
    filename = os.path.basename(filepath)  # just the filename, not full path
    filesize = os.path.getsize(filepath)   # size in bytes
    
    # Read file as bytes
    with open(filepath, 'rb') as f:
        filedata = f.read()
    
    # Telling server a file is coming
    send(FILE_MESSAGE)
    # Sending filename
    send(filename)
    # Sending filesize
    send(str(filesize))
    # Sending actual file data
    client.send(filedata)
    
    print(f"[SENT] {filename} ({filesize} bytes)")
    
        
def receive():
    while True:
        try:
            msg_length = client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(FORMAT)
                if msg == FILE_MESSAGE:
                    # Receive filename
                    msg_length = client.recv(HEADER).decode(FORMAT)
                    filename = client.recv(int(msg_length)).decode(FORMAT)
                    
                    # Receive filesize
                    msg_length = client.recv(HEADER).decode(FORMAT)
                    filesize = int(client.recv(int(msg_length)).decode(FORMAT))
                    
                    # Receive file data in chunks
                    filedata = b''
                    while len(filedata) < filesize:
                        chunk = client.recv(BUFFER)
                        if not chunk:
                            break
                        filedata += chunk
                    
                    # Save received file
                    with open(f"received_files/received_{filename}", 'wb') as f:
                        f.write(filedata)
                    
                    print(f"[RECEIVED] File saved as: received_{filename}")
                else:
                    print(msg)
                    
        except:
            print("[DISCONNECTED] Lost connection to server")
            break
        
        
# First thing — send username to server
username = input("Enter your username: ")
client.send(username.encode(FORMAT))


# Start receive thread
receive_thread = threading.Thread(target=receive)
receive_thread.daemon = True  # thread dies when main program exits
receive_thread.start()
    
    
# Main thread keeps taking input and sending
while True:
    msg = input()
    if msg == DISCONNECT_MESSAGE:
        send(DISCONNECT_MESSAGE)
        break
    
    elif msg.startswith("!SENDFILE"):
        # Usage: !SENDFILE path/to/file.jpg
        filepath = msg.split(" ", 1)[1]
        send_file(filepath)
        
    else:
        send(msg)
