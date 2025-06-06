from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import random
import signal
import sys

connected_clients = []  # All connected clients
waiting_clients = []  # Clients who have sent {enter_game}
pairs = {}  # client -> partner
addresses = {}

# New dictionaries for turn management
turns = {}  # client -> is_their_turn (bool)
colors = {}  # client -> color (True for white, False for black)

HOST = ''
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

# Flag to control server shutdown
server_running = True


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global server_running
    server_running = False

    # Close all client connections
    for client in connected_clients[:]:  # Use slice copy to avoid modification during iteration
        try:
            client.send(bytes("{info}Server is shutting down.", "utf8"))
            client.close()
        except:
            pass

    # Close server socket
    try:
        SERVER.close()
    except:
        pass

    print("Server shutdown complete.")
    sys.exit(0)


def accept_incoming_connections():
    global server_running
    while server_running:
        try:
            client, client_address = SERVER.accept()
            if not server_running:
                client.close()
                break

            print(f"{client_address} has connected.")
            addresses[client] = client_address
            connected_clients.append(client)
            Thread(target=handle_client, args=(client,)).start()
        except OSError:
            # Socket was closed, exit gracefully
            if not server_running:
                break
            else:
                print("Socket error in accept_incoming_connections")
                break


def try_pairing():
    """Try to pair two waiting clients and decide who starts first."""
    while len(waiting_clients) >= 2:
        player1 = waiting_clients.pop(0)
        player2 = waiting_clients.pop(0)

        # Randomly decide which player gets white (and thus goes first)
        player1_is_white = random.choice([True, False])

        # Set up the pairing
        pairs[player1] = player2
        pairs[player2] = player1

        # Assign colors
        colors[player1] = player1_is_white
        colors[player2] = not player1_is_white

        # Set initial turns (white always goes first)
        turns[player1] = player1_is_white
        turns[player2] = not player1_is_white

        # Notify both players of their color and turn status
        player1_color = "white" if player1_is_white else "black"
        player2_color = "black" if player1_is_white else "white"

        try:
            player1.send(bytes(f"{{info}}You are now paired. You are playing as {player1_color}.", "utf8"))
            player2.send(bytes(f"{{info}}You are now paired. You are playing as {player2_color}.", "utf8"))

            # Add a small delay to ensure color messages are processed first
            from time import sleep
            sleep(0.1)

            # Let players know whose turn it is
            if player1_is_white:
                player1.send(bytes("{turn}Your turn to move.", "utf8"))
                player2.send(bytes("{turn}Opponent's turn to move.", "utf8"))
            else:
                player1.send(bytes("{turn}Opponent's turn to move.", "utf8"))
                player2.send(bytes("{turn}Your turn to move.", "utf8"))

            # NEW: Start the synchronized clock for both players
            sleep(1)
            player1.send(bytes("{start_clock}", "utf8"))
            player2.send(bytes("{start_clock}", "utf8"))
        except:
            # If sending fails, clean up the pairing
            unpair(player1, notify_partner=False)


def unpair(client, notify_partner=True):
    """Unpair the client and optionally notify their partner."""
    partner = pairs.pop(client, None)
    if partner:
        pairs.pop(partner, None)
        # Also clean up the turns and colors data
        turns.pop(client, None)
        turns.pop(partner, None)
        colors.pop(client, None)
        colors.pop(partner, None)

        if notify_partner:
            try:
                partner.send(bytes("{info}Your partner has left the game.", "utf8"))
            except:
                pass


def handle_client(client):
    try:
        name = client.recv(BUFSIZ).decode("utf8")
    except:
        # Connection failed during initial handshake
        cleanup_client(client)
        return

    while server_running:
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
                    client.send(bytes("{info}You have left the game.", "utf8"))
                elif client in waiting_clients:
                    waiting_clients.remove(client)
                    client.send(bytes("{info}You have left the queue.", "utf8"))

            elif data == "{quit}":
                client.send(bytes("{quit}", "utf8"))
                break

            elif data.startswith("{move}"):
                partner = pairs.get(client)
                if not partner:
                    client.send(bytes("{error}No partner to send to.", "utf8"))
                    continue

                # Check if it's this client's turn
                if not turns.get(client, False):
                    client.send(bytes("{error}Not your turn to move.", "utf8"))
                    continue

                # If it is their turn, process the move
                # Switch turns
                turns[client] = False
                turns[partner] = True

                # Forward the move to the partner
                try:
                    partner.send(bytes(data, "utf8"))
                    # Notify both players of the turn change
                    client.send(bytes("{turn}Opponent's turn to move.", "utf8"))
                    partner.send(bytes("{turn}Your turn to move.", "utf8"))
                except:
                    # Partner connection failed
                    unpair(client, notify_partner=False)
                    client.send(bytes("{error}Partner disconnected.", "utf8"))

            else:
                # Handle regular chat messages
                partner = pairs.get(client)
                if partner:
                    try:
                        partner.send(bytes(data, "utf8"))
                    except:
                        # Partner connection failed
                        unpair(client, notify_partner=False)
                        client.send(bytes("{error}Partner disconnected.", "utf8"))
                else:
                    client.send(bytes("{error}No partner to send to.", "utf8"))

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            break

    # Cleanup on disconnect
    cleanup_client(client)


def cleanup_client(client):
    """Clean up client data when they disconnect"""
    if client in addresses:
        print(f"{addresses[client]} has disconnected.")
        del addresses[client]

    unpair(client, notify_partner=True)

    if client in waiting_clients:
        waiting_clients.remove(client)

    if client in connected_clients:
        connected_clients.remove(client)

    try:
        client.close()
    except:
        pass


if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        SERVER.listen(5)
        print("Waiting for connections...")

        ACCEPT_THREAD = Thread(target=accept_incoming_connections)
        ACCEPT_THREAD.daemon = True  # Make thread daemon so it dies with main process
        ACCEPT_THREAD.start()

        # Keep main thread alive
        while server_running:
            try:
                ACCEPT_THREAD.join(timeout=1)
                if not ACCEPT_THREAD.is_alive():
                    break
            except KeyboardInterrupt:
                signal_handler(signal.SIGINT, None)

    except Exception as e:
        print(f"Server error: {e}")
    finally:
        try:
            SERVER.close()
        except:
            pass
        print("Server stopped.")