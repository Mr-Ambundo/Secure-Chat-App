import socket
import threading
import sys

def encrypt_decrypt(message, key):
    return ''.join([chr(ord(c) ^ ord(key)) for c in message])

def receive_messages(client_socket):
    while True:
        try:
            msg = client_socket.recv(1024).decode()
            if not msg:
                print("\nConnection closed by server")
                break
                
            if msg.startswith("SERVER:"):
                #server broadcast
                decrypted = encrypt_decrypt(msg[7:], 'K')
                print(f"\n[System] {decrypted}\n[You] Send to: ", end="")
            else:
                # Regular message
                sender, encrypted = msg.split(':', 1)
                decrypted = encrypt_decrypt(encrypted, 'K')
                print(f"\n[{sender} -> You]: {decrypted}\n[You] Send to: ", end="")
                
        except Exception as e:
            print(f"\nError receiving message: {e}")
            break

def get_auth_choice():
    valid_choices = ['1', '2']  # Explicit list
    while True:
        print("\n1. Register\n2. Login")
        choice = input("Choose (1/2): ").strip()
        if choice in valid_choices:  # Checking list membership
            return 'register' if choice == '1' else 'login'
        print(f"Invalid choice. Must be one of {valid_choices}")

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('localhost', 9999))
    except:
        print("Could not connect to server")
        return

    mode = get_auth_choice()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    client.send(f"{mode}:{username}:{password}".encode())
    response = client.recv(1024).decode()
    
    if response not in ["REGISTER_SUCCESS", "LOGIN_SUCCESS"]:
        print(f"\nError: {response}")
        client.close()
        return

    print("\nAuthentication successful!")
    print("Commands:\n  /broadcast <message> - Send to everyone\n  /quit - Exit\n")
    
    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()
    
    try:
        while True:
            target = input("[You] Send to: ").strip()
            if target.lower() == '/quit':
                break
                
            if target.startswith('/broadcast '):
                message = target[len('/broadcast '):]
                client.send(f"/broadcast {message}".encode())
                continue
                
            message = input("[You] Message: ").strip()
            if message.lower() == '/quit':
                break
                
            encrypted = encrypt_decrypt(message, 'K')
            client.send(f"{target}:{encrypted}".encode())
            
    except KeyboardInterrupt:
        print("\nClosing connection...")
    finally:
        client.close()
        print("Disconnected")

if __name__ == "__main__":
    start_client()