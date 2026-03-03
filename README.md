# 🔐 SecureChat — TCP Chat Application

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

A fully featured secure chat application built from scratch using Python raw TCP sockets, SSL/TLS encryption, SQLite database, and bcrypt authentication.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [SSL Certificate Setup](#-ssl-certificate-setup)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Commands](#-commands)
- [How It Works](#-how-it-works)
- [Technical Concepts](#-technical-concepts)
- [Security](#-security)
- [Database Schema](#-database-schema)
- [Logging](#-logging)
- [Troubleshooting](#-troubleshooting)

---

## 📌 Overview

SecureChat is a multi-client TCP chat application that enables multiple users to communicate securely in real time over a network. It demonstrates core computer networking concepts including TCP/IP socket programming, SSL/TLS encryption, multi-threading, and persistent data storage.

```
Client 1 ──┐
Client 2 ──┼──► Secure Server (SSL) ──► SQLite Database
Client 3 ──┘         │
                      └──► server.log
```

---

## ✨ Features

### Core Chat Features

| Feature | Description |
|---------|-------------|
| Multi-client Support | Multiple users can connect simultaneously |
| Real-time Messaging | Instant message delivery to all connected users |
| Private Messaging | Send direct messages to specific users |
| File Transfer | Send files to all connected users |
| Message Timestamps | Every message shows exact time sent |
| Online Users List | View all currently connected users |
| Chat History | Last 10 messages shown when joining |
| Graceful Disconnect | Clean disconnection without server crash |

### Security Features

| Feature | Description |
|---------|-------------|
| SSL/TLS Encryption | All network traffic is fully encrypted |
| User Authentication | Secure register and login system |
| bcrypt Password Hashing | Passwords never stored in plain text |
| SQLite Database | Permanent storage for users and messages |
| Proper Logging | All activity saved to server.log with levels |
| Error Handling | Server stays running on unexpected errors |

---

## 📁 Project Structure

```
SecureChat/
│
├── server.py               # Main server — handles all clients
├── client.py               # Client — connects to server
│
├── cert.pem                # SSL certificate (share with clients)
├── key.pem                 # SSL private key  ⚠️ keep secret!
│
├── chat.db                 # SQLite database  (auto-created)
├── server.log              # Server activity log (auto-created)
│
├── server_files/           # Files received by server (auto-created)
│   └── server_received_*
│
├── received_files/         # Files received by client (auto-created)
│   └── received_*
│
└── README.md               # This file
```

---

## 📦 Requirements

### Python Version
```
Python 3.8 or higher
```

### Built-in Libraries (no installation needed)
```
socket      → TCP networking
ssl         → encryption
threading   → multi-client support
sqlite3     → database
logging     → server logs
datetime    → timestamps
os          → file operations
```

### External Libraries
```
bcrypt → password hashing
```

---

## ⚙️ Installation

**Step 1 — Install dependencies:**
```bash
pip install bcrypt
```

**Step 2 — Generate SSL certificate:**
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```
Press **Enter** for all questions.

**Step 3 — Copy cert.pem to client machine:**
```
cert.pem must be in the same folder as client.py
on every machine that wants to connect!
```

---

## 🔐 SSL Certificate Setup

| File | Purpose | Who has it |
|------|---------|------------|
| cert.pem | Public certificate | Server + all clients |
| key.pem | Private key | Server only! Never share! |

> ⚠️ **Important:** If key.pem is exposed, regenerate both files immediately.

---

## 🔧 Configuration

### Server Configuration (server.py)
```python
HEADER        = 64        # fixed header size in bytes
PORT          = 5050      # server port
SERVER        = "0.0.0.0" # listen on all interfaces
FORMAT        = 'utf-8'   # encoding format
BUFFER        = 1024      # file transfer chunk size
HISTORY_LIMIT = 10        # messages shown to new clients
DATABASE_FILE = "chat.db"
CERT_FILE     = "cert.pem"
KEY_FILE      = "key.pem"
```

### Client Configuration (client.py)
```python
SERVER    = "192.168.1.7"  # change to server's IP address
PORT      = 5050           # must match server port
CERT_FILE = "cert.pem"     # must be same cert as server
```

---

## 🚀 Running the Application

### Start the Server

```bash
python server.py
```

Expected output:
```
2026-03-01 10:35:22 - INFO - Secure server is starting...
2026-03-01 10:35:22 - INFO - Database initialized
2026-03-01 10:35:22 - INFO - SSL context created
2026-03-01 10:35:22 - INFO - Secure server listening on port 5050
```

### Start the Client

```bash
python client.py
```

Expected output:
```
[CONNECTED] Secure connection established

========================================
        WELCOME TO SECURECHAT
========================================
1. Login
2. Register
========================================
Enter choice (1 or 2):
```

### First Time — Register
```
Enter choice: 2
Choose username: Meet
Choose password: yourpassword

[SERVER] Registration successful!
```

### Returning User — Login
```
Enter choice: 1
Username: Meet
Password: yourpassword

[SERVER] Login successful!
```

### Connecting Over LAN

Update `client.py`:
```python
SERVER = "192.168.x.x"  # server machine's local IP
```

Find server's local IP:
```bash
# Windows
ipconfig

# Linux / Mac
ifconfig
```

---

## 💬 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!DISCONNECT` | Leave the chat gracefully | `!DISCONNECT` |
| `!USERS` | Show all online users | `!USERS` |
| `!DM <username> <message>` | Send private message | `!DM John Hey!` |
| `!SENDFILE <filepath>` | Send file to all users | `!SENDFILE photo.jpg` |

### Examples
```bash
# Send a private message
!DM John Hey John, can you see this?

# Send a file
!SENDFILE C:\Users\Meet\Documents\notes.pdf

# See who is online
!USERS

# Leave the chat
!DISCONNECT
```

---

## ⚙️ How It Works

### Connection and Authentication Flow
```
Client                          Server
──────                          ──────
connect()           ──────►     accept()
                                    │
SSL handshake   ◄──────────────►    │  (encrypt connection)
                                    │
send(!REGISTER)     ──────►     authenticate_client()
send(username)      ──────►         │
send(password)      ──────►     register_user()
                                    │  hash password with bcrypt
                                    │  save to database
recv(response)  ◄──────────    send("Registration successful!")
                                    │
recv(history)   ◄──────────    send_history()
                                    │
                                Real-time chat begins!
```

### Message Protocol

Every message uses a fixed 64-byte header:
```
┌──────────────────────────────────┬──────────────────────────┐
│   HEADER (64 bytes)              │   MESSAGE (variable)     │
│   contains message length        │   actual content         │
│   padded with spaces             │                          │
└──────────────────────────────────┴──────────────────────────┘

Example:
Header:  "48                              " (padded to 64 bytes)
Message: "[10:35 AM] [Meet] Hello everyone!" (48 bytes)
```
Fixed header tells server exactly how many bytes to read — prevents TCP fragmentation.

### File Transfer Protocol
```
Sender                      Server                    Receivers
──────                      ──────                    ─────────
send("!FILE")   ──────►
send(filename)  ──────►
send(filesize)  ──────►
send(filedata)  ──────►     save file locally
  (in chunks)               broadcast_file()  ──────►  receive chunks
                                                        save to received_files/
```

### Threading Model
```
Main Thread
    │
    ├── Client Thread 1 ─── Meet  (handle_client)
    ├── Client Thread 2 ─── John  (handle_client)
    └── Client Thread 3 ─── Alice (handle_client)
```
Each client runs on its own thread — one client never blocks another.

---

## 🧠 Technical Concepts

**TCP/IP**
Uses TCP (Transmission Control Protocol) for reliable, ordered, error-checked delivery of data between client and server. All messages arrive in the correct order without data loss.

**SSL/TLS Encryption**
All data between client and server is encrypted. Even if someone intercepts the traffic, they see only unreadable encrypted data.
```
Without SSL:  "Hello John"  ──► network ──► "Hello John"   (readable!)
With SSL:     "Hello John"  ──► network ──► "$#@!Kj3x9mQ"  (encrypted!)
```

**Multi-threading**
Each client connection runs on a dedicated Python thread. This allows the server to handle multiple simultaneous connections without any client blocking another.

**bcrypt Password Hashing**
Passwords are never stored in plain text. bcrypt adds a random salt before hashing — the same password always produces a different hash, defeating rainbow table attacks.
```
password: "1234"  ──► bcrypt ──► "$2b$12$Kj3x9mQ..."  (stored in DB)
```

**SQLite Database**
All user accounts and messages are stored permanently in chat.db. Data survives server restarts. Parameterized queries prevent SQL injection.

**Logging**
All server activity is logged to server.log using Python's logging module with severity levels INFO, WARNING, and ERROR.

---

## 🔒 Security

| Security Feature | Implementation | Protection Against |
|-----------------|---------------|-------------------|
| SSL/TLS | ssl.SSLContext | Network eavesdropping |
| bcrypt hashing | bcrypt.hashpw | Password theft |
| Parameterized SQL | cursor.execute("?") | SQL injection |
| Authentication | login_user() | Unauthorized access |
| Duplicate login check | username in usernames | Account sharing |
| Error handling | try/except everywhere | Server crashes |

---

## 📊 Database Schema

```sql
CREATE TABLE users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT    UNIQUE NOT NULL,
    password   TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE TABLE messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sender     TEXT    NOT NULL,
    message    TEXT    NOT NULL,
    timestamp  TEXT    NOT NULL
);
```

---

## 📝 Logging

All activity saved to `server.log`:

```
2026-03-01 10:35:22 - INFO    - Secure server is starting...
2026-03-01 10:35:22 - INFO    - Database initialized
2026-03-01 10:35:22 - INFO    - SSL context created
2026-03-01 10:35:22 - INFO    - Secure server listening on port 5050
2026-03-01 10:35:45 - INFO    - New connection from ('192.168.1.5', 54321)
2026-03-01 10:35:46 - INFO    - New user registered: Meet
2026-03-01 10:35:46 - INFO    - Meet authenticated and joined
2026-03-01 10:36:12 - INFO    - Meet: Hello everyone!
2026-03-01 10:36:30 - INFO    - Meet sent file: photo.jpg (204800 bytes)
2026-03-01 10:36:45 - WARNING - Failed login attempt for: unknown_user
2026-03-01 10:37:00 - INFO    - Meet disconnected
```

| Level | Meaning |
|-------|---------|
| INFO | Normal activity |
| WARNING | Suspicious or unusual event |
| ERROR | Something failed but server continues |

---

## 🔧 Troubleshooting

**"Address already in use"**
```python
PORT = 5051  # change port in server.py
```

**"Connection refused"**
```
→ Make sure server.py is running first
→ Check SERVER IP in client.py
→ Check firewall allows the port
```

**"Certificate verify failed"**
```
→ cert.pem must be in client folder
→ Must match server's cert.pem exactly
→ Regenerate if expired (after 365 days)
```

**"Module not found: bcrypt"**
```bash
pip install bcrypt
```

**"openssl not recognized" (Windows)**
```bash
$env:Path += ";C:\Program Files\OpenSSL-Win64\bin"
```

---

## 👨‍💻 Built With

| Library | Purpose |
|---------|---------|
| socket | Raw TCP networking |
| ssl | TLS/SSL encryption |
| threading | Multi-client support |
| sqlite3 | Persistent database |
| bcrypt | Password hashing |
| logging | Server activity logs |
| datetime | Message timestamps |
| os | File system operations |

---

## 📄 License

This project is open source and available under the MIT License.

Copyright (c) 2026 Meet Italiya

---

*Built as a computer networks project demonstrating TCP/IP socket programming,
SSL/TLS encryption, multi-threading, authentication, and database integration.*