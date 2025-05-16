import tkinter as tk
import ttkbootstrap as ttk
from PIL import Image, ImageTk
import chess
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

# Constants
BOARD_SIZE = 800
SQUARE_SIZE = BOARD_SIZE // 8
PIECE_SIZE_TO_SQUARE = 15
COLORS = {'odd': '#83CB72', 'even': '#DCE2D6'}
CIRCLE_CONST = 35

# Socket constants
HOST = '127.0.0.1'
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

# Global variables
piece_images = {}
board = chess.Board()
game_state = {"selected": None, "current_player": chess.WHITE}
chat_display = None  # Will be set in start_game()
client_socket = None
receive_thread = None


# Client functions
def connect_to_server(username="Player1"):
    """Connect to the chess server"""
    global client_socket, receive_thread

    client_socket = socket(AF_INET, SOCK_STREAM)
    try:
        client_socket.connect(ADDR)
        client_socket.send(bytes(username, "utf8"))

        # Start receiving thread
        receive_thread = Thread(target=receive_messages, daemon=True)
        receive_thread.start()
        return True
    except Exception as e:
        print(f"Connection error: {e}")
        return False


def receive_messages():
    """Continuously receive messages from the server"""
    global chat_display

    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            if not msg:
                break

            print(f"Server: {msg}")

            # Check if chat_display exists and update it
            if chat_display and chat_display.winfo_exists():
                chat_display.configure(state="normal")
                chat_display.insert(tk.END, f"Opponent: {msg}\n")
                chat_display.configure(state="disabled")
                chat_display.see(tk.END)

            # Check if the message is a move
            if msg.startswith("{move}"):
                move_text = msg[6:]  # Remove {move} prefix
                process_opponent_move(move_text)

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print("Connection lost.")
            break


def send_message(msg):
    """Send a message to the server"""
    try:
        if client_socket:
            client_socket.send(bytes(msg, "utf8"))
    except OSError:
        print("Error sending message.")


def stop_client():
    """Close the client connection"""
    if client_socket:
        send_message("{quit}")
        client_socket.close()


def process_opponent_move(move_text):
    """Process an opponent's move from text representation"""
    global board, game_state, chat_display

    try:
        # Convert text to chess.Move
        move = chess.Move.from_uci(move_text)

        # Apply the move to our board
        if move in board.legal_moves:
            board.push(move)
            game_state["current_player"] = not game_state["current_player"]

            # Update the board display if it exists
            # This needs to be handled carefully since we're in a separate thread
            # and need to update the UI from the main thread
    except Exception as e:
        print(f"Error processing opponent move: {e}")


# Chess graphics functions
def load_images():
    """Load chess piece images"""
    piece_names = {
        'r': "white rook",
        'n': "white knight",
        'b': "white bishop",
        'q': "white queen",
        'k': "white king",
        'p': "white pawn",
        'R': "black rook",
        'N': "black knight",
        'B': "black bishop",
        'Q': "black queen",
        'K': "black king",
        'P': "black pawn",
    }

    for key, name in piece_names.items():
        img = Image.open(f"assets/pieces/{name}.png")
        img = img.resize((SQUARE_SIZE - PIECE_SIZE_TO_SQUARE, SQUARE_SIZE - PIECE_SIZE_TO_SQUARE))
        piece_images[key] = ImageTk.PhotoImage(img)


def draw_board(canvas):
    """Draw the chess board squares"""
    for row in range(8):
        for col in range(8):
            color = COLORS['odd'] if (row + col) % 2 == 0 else COLORS['even']
            canvas.create_rectangle(col * SQUARE_SIZE, row * SQUARE_SIZE, (col + 1) * SQUARE_SIZE,
                                    (row + 1) * SQUARE_SIZE, fill=color, outline="")


def draw_pieces(canvas, fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
    """Draw chess pieces on the board based on FEN notation"""
    board_fen = fen.split()[0].replace('/', '')
    i = 0
    for piece_fen_representation in board_fen:
        if piece_fen_representation.isdigit():
            i += int(piece_fen_representation)
        else:
            canvas.create_image((i % 8) * SQUARE_SIZE + PIECE_SIZE_TO_SQUARE / 2,
                                (i // 8) * SQUARE_SIZE + PIECE_SIZE_TO_SQUARE / 2, anchor="nw",
                                image=piece_images[piece_fen_representation])
            i += 1


def on_square_click(event, canvas, chess_board, game_state, return_to_homescreen):
    """Handle click events on the chess board"""
    row = event.y // SQUARE_SIZE
    col = event.x // SQUARE_SIZE
    square = chess.square(col, 7 - row)
    piece = chess_board.piece_at(square)

    if game_state["selected"]:
        move = chess.Move(game_state["selected"], square)
        if move in chess_board.legal_moves:
            chess_board.push(move)
            game_state["selected"] = None
            game_state["current_player"] = not game_state["current_player"]

            # Send the move to the opponent
            send_message(f"{{move}}{move}")

            # Check for game over
            if chess_board.is_game_over():
                print("Game over!")
                canvas.after(2000,
                             lambda: show_game_over_screen(canvas, game_result(chess_board), return_to_homescreen))
        else:
            game_state["selected"] = square
    elif piece and piece.color == game_state["current_player"]:
        game_state["selected"] = square

    update_board(canvas, chess_board, game_state)


def game_result(chess_board):
    """Determine the game result text"""
    if chess_board.result() == "1-0":
        result_text = "White wins!"
    elif chess_board.result() == "0-1":
        result_text = "Black wins!"
    else:
        result_text = "Draw!"

    return result_text


def update_board(canvas, chess_board, game_state):
    """Update the board display with current game state"""
    canvas.delete("all")
    draw_board(canvas)
    draw_pieces(canvas, chess_board.fen())

    # Highlight selected square
    if game_state["selected"]:
        row = 7 - chess.square_rank(game_state["selected"])
        col = chess.square_file(game_state["selected"])
        x1 = col * SQUARE_SIZE
        y1 = row * SQUARE_SIZE
        x2 = x1 + SQUARE_SIZE
        y2 = y1 + SQUARE_SIZE
        canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3)

        for move in chess_board.legal_moves:
            if move.from_square == game_state["selected"]:
                row = 7 - move.to_square // 8
                col = move.to_square % 8
                x1 = col * SQUARE_SIZE
                y1 = row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                canvas.create_oval(x1 + CIRCLE_CONST, y1 + CIRCLE_CONST, x2 - CIRCLE_CONST, y2 - CIRCLE_CONST,
                                   fill="gray")


def start_game(window, return_to_homescreen):
    """Start a new chess game"""
    global chat_display, board, game_state

    # Reset the game state
    board = chess.Board()
    game_state = {"selected": None, "current_player": chess.WHITE}

    # Notify server that we're entering a game
    send_message("{enter_game}")

    # Hide home screen
    for widget in window.winfo_children():
        widget.pack_forget()
        widget.place_forget()

    # Create background frame and canvas
    bg_frame = tk.Frame(window)
    bg_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(bg_frame, width=500, height=500)
    canvas.pack(fill="both", expand=True)

    # Load images
    bg_image = ImageTk.PhotoImage(
        Image.open("assets/utils/chessBackground.jpg").resize(
            (window.winfo_screenwidth(), window.winfo_screenheight()))
    )

    # Place background image
    canvas.bg_image = bg_image  # Save reference!
    canvas.create_image(0, 0, image=bg_image, anchor=tk.NW)

    # === Create Chess Canvas ===
    chess_canvas = tk.Canvas(canvas, width=BOARD_SIZE, height=BOARD_SIZE, bd=5, relief="ridge")
    chess_canvas.place(relx=0.5, rely=0.5, anchor="center")

    # Load images and draw board
    load_images()

    draw_board(chess_canvas)
    draw_pieces(chess_canvas)

    # Bind clicks
    chess_canvas.bind("<Button-1>",
                      lambda event: on_square_click(event, chess_canvas, board, game_state, return_to_homescreen))

    # === Create Buttons (Draw, Resign) ===
    draw_button = tk.Button(canvas, text="Offer Draw", width=15)
    resign_button = tk.Button(canvas, text="Resign", width=15, command=return_to_homescreen)

    canvas.create_window(window.winfo_screenwidth() / 2 + 100, window.winfo_screenheight() / 2 + BOARD_SIZE / 2 + 25,
                         window=draw_button)
    canvas.create_window(window.winfo_screenwidth() / 2 - 100, window.winfo_screenheight() / 2 + BOARD_SIZE / 2 + 25,
                         window=resign_button)

    # === Left: Chat Frame ===
    chat_frame = tk.Frame(canvas, bg="white", bd=5, relief="ridge")
    canvas.create_window(window.winfo_screenwidth() / 2 - BOARD_SIZE / 2 - 150, window.winfo_screenheight() / 2,
                         window=chat_frame)  # Adjust position

    # Chat display area
    global chat_display
    chat_display = tk.Text(chat_frame, height=40, width=30, state="disabled", bg="white", wrap="word")
    chat_display.grid(row=0, column=0, padx=5, pady=5)

    # Entry field for typing
    chat_entry = tk.Entry(chat_frame, width=30)
    chat_entry.grid(row=1, column=0, padx=5, pady=5)

    def send_chat_message(event=None):
        message = chat_entry.get()
        if message.strip() != "":
            chat_display.configure(state="normal")
            chat_display.insert(tk.END, f"You: {message}\n")
            chat_display.configure(state="disabled")
            chat_display.see(tk.END)

            # Send the message to the server
            send_message(message)

            chat_entry.delete(0, tk.END)

    chat_entry.bind("<Return>", send_chat_message)


def show_game_over_screen(canvas, result_text, return_to_homescreen):
    """Display game over screen with result"""
    # Center of the canvas
    center_x = canvas.winfo_width() / 2
    center_y = canvas.winfo_height() / 2

    rect_width = 300
    rect_height = 400

    # Draw a semi-transparent dark rectangle behind everything (optional)
    canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(),
                            fill="#000000", stipple="gray50", outline="")

    # Draw rounded rectangle
    create_rounded_rectangle(
        canvas,
        center_x - rect_width / 2,
        center_y - rect_height / 2,
        center_x + rect_width / 2,
        center_y + rect_height / 2,
        radius=40,
        fill="#111111",
        outline="#333333",
        width=2
    )

    # Draw game result text
    canvas.create_text(center_x, center_y - rect_height / 4,
                       text=result_text, font=("Arial", 24, "bold"), fill="white")

    # Create "Return Home" button directly on the canvas
    return_button = tk.Button(canvas, text="Return Home", font=("Arial", 14),
                              command=return_to_homescreen)
    canvas.create_window(center_x, center_y + rect_height / 4, window=return_button)


def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Draw a rounded rectangle on the canvas"""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)


# Initialize the client connection when this module is imported
def initialize():
    connect_to_server()


initialize()