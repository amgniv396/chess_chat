'''#!/usr/bin/env python3
"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import random
from datetime import datetime

def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s has connected." % client_address)
        client.send(bytes("Greetings from the cave! Now type your name and press enter!", "utf8"))
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()

def send_rand(client):
    number = str(random.randint(0,10))
    client.send(bytes(number, "utf8"))
def send_time(client):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    client.send(bytes(current_time, "utf8"))
def send_name(client):
    name = clients[client]
    client.send(bytes(name, "utf8"))

def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""

    name = client.recv(BUFSIZ).decode("utf8")
    if name == "{quit}":
        client.close()
        return
    welcome = 'Welcome %s! If you ever want to quit, type {quit} to exit.' % name
    client.send(bytes(welcome, "utf8"))
    msg = "%s has joined the chat!" % name
    broadcast(bytes(msg, "utf8"))
    clients[client] = name

    while True:
        msg = client.recv(BUFSIZ)
        if msg != bytes("{quit}", "utf8"):
            if msg == bytes("{rand}", "utf8"):
                send_rand(client)
            elif msg == bytes("{time}", "utf8"):
                send_time(client)
            elif msg == bytes("{name}", "utf8"):
                send_name(client)
            else:
                broadcast(msg, name + ": ")
        else:
            client.close()
            del clients[client]
            broadcast(bytes("%s has left the chat." % name, "utf8"))
            break


def broadcast(msg, prefix=""):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""

    for sock in clients:
        sock.send(bytes(prefix, "utf8") + msg)


clients = {}
addresses = {}

HOST = ''
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connection...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()'''

# !/usr/bin/env python3
"""Server for paired client communication in a game."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

clients = []
pairs = {}
addresses = {}

HOST = ''
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)


def accept_incoming_connections():
    """Handles incoming client connections and pairs them."""
    while True:
        client, client_address = SERVER.accept()
        print(f"{client_address} has connected.")
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):
    """Handles a single client connection and pairs them."""
    name = client.recv(BUFSIZ).decode("utf8")
    print(f"{name} has joined.")

    clients.append(client)

    # Wait for a pair
    if len(clients) % 2 == 0:
        player1 = clients[-2]
        player2 = clients[-1]
        pairs[player1] = player2
        pairs[player2] = player1
        player1.send(bytes("{info}You are now paired.", "utf8"))
        player2.send(bytes("{info}You are now paired.", "utf8"))
    else:
        client.send(bytes("{info}Waiting for a pair...", "utf8"))

    while True:
        try:
            data = client.recv(BUFSIZ).decode("utf8")
            if not data:
                break

            if data.startswith("{quit}"):
                client.send(bytes("{quit}", "utf8"))
                break

            partner = pairs.get(client)
            if partner:
                partner.send(bytes(data, "utf8"))
            else:
                client.send(bytes("{error}No partner yet.", "utf8"))

        except (ConnectionResetError, ConnectionAbortedError):
            break

    # Cleanup on disconnect
    print(f"{addresses[client]} has disconnected.")
    partner = pairs.get(client)
    if partner:
        partner.send(bytes("{info}Your partner has disconnected.", "utf8"))
        del pairs[partner]
    if client in pairs:
        del pairs[client]
    if client in clients:
        clients.remove(client)
    client.close()


if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connections...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
