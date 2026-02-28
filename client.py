import socket

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
    
# First thing — send username to server
username = input("Enter your username: ")
client.send(username.encode(FORMAT))

    
send("Hello World!")
input()
send("Hello Everyone!")
input()
send("Hello Meet!")

send(DISCONNECT_MESSAGE)