from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

connected_clients = []  # All connected clients
waiting_clients = []    # Clients who have sent {enter_game}
pairs = {}              # client -> partner
addresses = {}

HOST = ''
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)


def accept_incoming_connections():
    while True:
        client, client_address = SERVER.accept()
        print(f"{client_address} has connected.")
        addresses[client] = client_address
        connected_clients.append(client)
        Thread(target=handle_client, args=(client,)).start()


def try_pairing():
    """Try to pair two waiting clients."""
    while len(waiting_clients) >= 2:
        player1 = waiting_clients.pop(0)
        player2 = waiting_clients.pop(0)
        pairs[player1] = player2
        pairs[player2] = player1
        player1.send(bytes("{info}You are now paired.", "utf8"))
        player2.send(bytes("{info}You are now paired.", "utf8"))


def unpair(client, notify_partner=True):
    """Unpair the client and optionally notify their partner."""
    partner = pairs.pop(client, None)
    if partner:
        pairs.pop(partner, None)
        if notify_partner:
            try:
                partner.send(bytes("{info}Your partner has left the game.", "utf8"))
            except:
                pass
            '''# Move the partner back to the waiting list
            if partner not in waiting_clients:
                waiting_clients.append(partner)
            try_pairing()'''


def handle_client(client):
    name = client.recv(BUFSIZ).decode("utf8")
    print(f"{name} has joined.")
    client.send(bytes("{info}Welcome! Send {enter_game} to start pairing.", "utf8"))

    while True:
        try:
            data = client.recv(BUFSIZ).decode("utf8")
            if not data:
                break

            if data == "{enter_game}":
                if client not in waiting_clients and client not in pairs:
                    waiting_clients.append(client)
                    client.send(bytes("{info}Looking for a partner...", "utf8"))
                    try_pairing()

            elif data == "{quit_game}":
                if client in pairs:
                    unpair(client, notify_partner=True)
                    client.send(bytes("{info}You have left the game. Send {enter_game} to find a new match.", "utf8"))
                elif client in waiting_clients:
                    waiting_clients.remove(client)
                    client.send(bytes("{info}You have left the queue. Send {enter_game} to rejoin.", "utf8"))
                else:
                    client.send(bytes("{info}You are not in a game or queue.", "utf8"))

            elif data == "{quit}":
                client.send(bytes("{quit}", "utf8"))
                break

            else:
                partner = pairs.get(client)
                if partner:
                    partner.send(bytes(data, "utf8"))
                else:
                    client.send(bytes("{error}No partner to send to.", "utf8"))

        except (ConnectionResetError, ConnectionAbortedError):
            print('error')
            break

    # Cleanup on disconnect
    print(f"{addresses[client]} has disconnected.")
    unpair(client, notify_partner=True)
    if client in waiting_clients:
        waiting_clients.remove(client)
    if client in connected_clients:
        connected_clients.remove(client)
    client.close()




if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connections...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
