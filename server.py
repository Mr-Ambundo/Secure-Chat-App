import socket
import threading
from ast import literal_eval

def encrypt_decrypt(message, key):
    return ''.join([chr(ord(c) ^ ord(key)) for c in message])

def load_users():
    try:
        with open('users.txt', 'r') as f:
            return literal_eval(f.read())
    except:
        return {}

def save_users(users):
    with open('users.txt', 'w') as f:
        f.write(str(users))

users = load_users()
active_clients = {}

def broadcast(message, exclude_user=None):
    """Send message to all connected clients except exclude_user"""
    encrypted = encrypt_decrypt(message, 'K')
    for username, client_socket in active_clients.items():
        if username != exclude_user:
            try:
                client_socket.send(f"SERVER:{encrypted}".encode())
            except:
                continue

def handle_client(client_socket):
    username = None
    try:
        # Authentication phase
        while True:
            auth_attempt = client_socket.recv(1024).decode()
            if not auth_attempt:
                break
            
            parts = auth_attempt.split(':')
            if len(parts) != 3:
                client_socket.send("INVALID_FORMAT".encode())
                continue
                
            mode, username, password = parts
            
            if mode == 'register':
                if len(users) >= 3:
                    client_socket.send("MAX_USERS_REACHED".encode())
                    break
                if username in users:
                    client_socket.send("USERNAME_EXISTS".encode())
                    continue
                users[username] = password
                save_users(users)
                client_socket.send("REGISTER_SUCCESS".encode())
                broadcast(f"{username} has joined the chat!")
                break
                
            elif mode == 'login':
                if users.get(username) == password:
                    if username in active_clients:
                        client_socket.send("ALREADY_LOGGED_IN".encode())
                        continue
                    client_socket.send("LOGIN_SUCCESS".encode())
                    broadcast(f"{username} has reconnected!")
                    break
                else:
                    client_socket.send("LOGIN_FAILED".encode())
                    continue
                    
            else:
                client_socket.send("INVALID_MODE".encode())
                continue

        if username:
            active_clients[username] = client_socket
            
            # Chat loop
            while True:
                msg = client_socket.recv(1024).decode()
                if not msg: break
                
                if msg.startswith("/broadcast "):
                    message = msg[len("/broadcast "):]
                    broadcast(f"{username} (broadcast): {message}", username)
                else:
                    target, encrypted_msg = msg.split(':', 1)
                    if target in active_clients:
                        decrypted = encrypt_decrypt(encrypted_msg, 'K')
                        encrypted = encrypt_decrypt(decrypted, 'K')
                        active_clients[target].send(f"{username}:{encrypted}".encode())
                        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if username and username in active_clients:
            del active_clients[username]
            broadcast(f"{username} has left the chat")
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999))
    server.listen(3)
    print("Server started, waiting for connections...")
    
    while True:
        client, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

if __name__ == "__main__":
    start_server()