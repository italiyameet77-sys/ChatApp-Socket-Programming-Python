import socket
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext

HEADER = 64
PORT = 8080
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
FILE_MESSAGE = "!FILE"
SERVER = "192.168.31.248"
ADDR = (SERVER, PORT)
BUFFER = 1024

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

# ─────────────────────────────────────
# NETWORK FUNCTIONS
# ─────────────────────────────────────

def send_message(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def send_file(filepath):
    import os
    if not os.path.exists(filepath):
        show_message("[ERROR] File not found!")
        return

    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)

    with open(filepath, 'rb') as f:
        filedata = f.read()

    send_message(FILE_MESSAGE)
    send_message(filename)
    send_message(str(filesize))
    client.send(filedata)

    show_message(f"[YOU] sent file: {filename}")

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

                    # Receive file data
                    filedata = b''
                    while len(filedata) < filesize:
                        chunk = client.recv(BUFFER)
                        if not chunk:
                            break
                        filedata += chunk

                    # Save file
                    import os
                    os.makedirs("received_files", exist_ok=True)
                    with open(f"received_files/received_{filename}", 'wb') as f:
                        f.write(filedata)

                    show_message(f"[FILE RECEIVED] saved as: received_{filename}")

                else:
                    show_message(msg)

        except:
            show_message("[DISCONNECTED] Lost connection to server")
            break

# ─────────────────────────────────────
# GUI FUNCTIONS
# ─────────────────────────────────────

def show_message(msg):
    # Enable → insert → disable (read only)
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, msg + "\n")
    chat_area.yview(tk.END)  # auto scroll to bottom
    chat_area.config(state=tk.DISABLED)

def on_send():
    msg = message_input.get()
    if msg == "":
        return
    if msg == DISCONNECT_MESSAGE:
        send_message(DISCONNECT_MESSAGE)
        window.destroy()
        return

    send_message(msg)
    show_message(f"[YOU] {msg}")  # show your own message
    message_input.delete(0, tk.END)  # clear input box

def on_send_file():
    # Open file picker dialog
    filepath = filedialog.askopenfilename(
        title="Select a file",
        filetypes=[
            ("All files", "*.*"),
            ("Images", "*.png *.jpg *.jpeg"),
            ("Documents", "*.pdf *.docx *.txt")
        ]
    )
    if filepath:
        send_file(filepath)

def on_enter_key(event):
    on_send()  # send message when Enter key is pressed

# ─────────────────────────────────────
# LOGIN WINDOW
# ─────────────────────────────────────

def start_chat():
    username = username_input.get()
    if username == "":
        return

    # Send username to server
    client.send(username.encode(FORMAT))

    # Close login window
    login_window.destroy()

    # Open chat window
    open_chat_window(username)

login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("300x150")
login_window.resizable(False, False)

tk.Label(login_window, text="Enter your username:", font=("Arial", 12)).pack(pady=10)
username_input = tk.Entry(login_window, font=("Arial", 12), width=20)
username_input.pack(pady=5)
tk.Button(login_window, text="Join Chat", font=("Arial", 12), command=start_chat).pack(pady=10)

# ─────────────────────────────────────
# CHAT WINDOW
# ─────────────────────────────────────

def open_chat_window(username):
    global chat_area, message_input, window

    window = tk.Tk()
    window.title(f"Chat Room — {username}")
    window.geometry("500x600")
    window.resizable(False, False)

    # ── Top: Chat Area ──
    chat_frame = tk.Frame(window)
    chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    chat_area = scrolledtext.ScrolledText(
        chat_frame,
        state=tk.DISABLED,
        font=("Arial", 11),
        bg="#f0f0f0",
        wrap=tk.WORD
    )
    chat_area.pack(fill=tk.BOTH, expand=True)

    # ── Bottom: Input Area ──
    input_frame = tk.Frame(window)
    input_frame.pack(padx=10, pady=5, fill=tk.X)

    message_input = tk.Entry(
        input_frame,
        font=("Arial", 11),
        width=35
    )
    message_input.pack(side=tk.LEFT, padx=5)
    message_input.bind("<Return>", on_enter_key)  # Enter key sends message

    send_button = tk.Button(
        input_frame,
        text="Send",
        font=("Arial", 11),
        width=8,
        command=on_send
    )
    send_button.pack(side=tk.LEFT, padx=5)

    # ── File Button ──
    file_frame = tk.Frame(window)
    file_frame.pack(padx=10, pady=5, fill=tk.X)

    file_button = tk.Button(
        file_frame,
        text="📎 Send File",
        font=("Arial", 11),
        width=15,
        command=on_send_file
    )
    file_button.pack(side=tk.LEFT, padx=5)

    # Start receive thread
    receive_thread = threading.Thread(target=receive)
    receive_thread.daemon = True
    receive_thread.start()

    window.mainloop()

login_window.mainloop()
