from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

HOST = '127.0.0.1'
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)
client_socket.send(bytes("Player1", "utf8"))  # Send a name immediately


def receive():
    """Handles receiving of messages."""
    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            print(f"Server: {msg}")
        except OSError:
            break

def send(msg):
    """Sends a message to the server."""
    client_socket.send(bytes(msg, "utf8"))
    if msg == "{quit}":
        client_socket.close()

# Start receiving thread
receive_thread = Thread(target=receive, daemon=True)
receive_thread.start()
