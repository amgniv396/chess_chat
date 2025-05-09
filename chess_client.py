# chess_client_module.py
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

HOST = '127.0.0.1'
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)
client_socket.send(bytes("Player1", "utf8"))  # Send name when connecting #TODO:get name
def receive():
    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            if not msg:
                break
            print(f"Server: {msg}")
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print("Connection lost.")
            break

receive_thread = Thread(target=receive, daemon=True)
receive_thread.start()

def send_message(msg):
    """Send a message to the server."""
    #TODO: check for BUFSIZ
    try:
        client_socket.send(bytes(msg, "utf8"))
    except OSError:
        pass

def stop_client():
    send_message("{quit}")
    client_socket.close()
