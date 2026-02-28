import socket
import threading

HEADER = 64
PORT = 8080
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.31.248"
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    
    
def receive():
    while True:
        try:
            msg_length = client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(FORMAT)
                print(msg)  # print server's reply
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
    send(msg)
