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
game_state = {
    "selected": None,
    "current_player": chess.WHITE,  # White always starts in chess
    "my_color": None,  # Will be set when paired (True for white, False for black)
    "my_turn": False,  # Will be set when paired based on color
    "promotion_ui_active": False,  # Flag to track when promotion UI is visible
    "promotion_move": None,  # Store the potential promotion move
}
chat_display = None  # Will be set in start_game()
status_label = None  # Will display turn status
client_socket = None
receive_thread = None
chess_canvas = None  # Added global reference to the chess canvas


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
    global chat_display, chess_canvas, game_state, status_label

    while True:
        try:
            msg = client_socket.recv(BUFSIZ).decode("utf8")
            if not msg:
                break

            print(f"Server: {msg}")

            # Handle info messages
            if msg.startswith("{info}"):
                info_msg = msg[6:]  # Remove {info} prefix
                if chat_display and chat_display.winfo_exists():
                    chat_display.configure(state="normal")
                    chat_display.insert(tk.END, f"System: {info_msg}\n")
                    chat_display.configure(state="disabled")
                    chat_display.see(tk.END)

                # Check if the message contains color assignment
                if "You are playing as white" in info_msg:
                    game_state["my_color"] = True  # White
                    # Update status if this is the first player
                    if status_label and status_label.winfo_exists():
                        status_label.config(text="Waiting for opponent...")
                elif "You are playing as black" in info_msg:
                    game_state["my_color"] = False  # Black
                    # Update status if this is the second player
                    if status_label and status_label.winfo_exists():
                        status_label.config(text="Waiting for opponent...")

            # Handle turn notifications
            elif msg.startswith("{turn}"):
                turn_msg = msg[6:]  # Remove {turn} prefix
                if chat_display and chat_display.winfo_exists():
                    chat_display.configure(state="normal")
                    chat_display.insert(tk.END, f"System: {turn_msg}\n")
                    chat_display.configure(state="disabled")
                    chat_display.see(tk.END)

                # Update turn status
                game_state["my_turn"] = "Your turn" in turn_msg

                # Update status label if it exists
                if status_label and status_label.winfo_exists():
                    status_text = "Your turn" if game_state["my_turn"] else "Opponent's turn"
                    status_label.config(text=status_text)

                # Force update the board to reflect turn status visually
                if chess_canvas and chess_canvas.winfo_exists():
                    chess_canvas.after(0, lambda: update_board(chess_canvas, board, game_state))

            # Handle error messages
            elif msg.startswith("{error}"):
                error_msg = msg[7:]  # Remove {error} prefix
                if chat_display and chat_display.winfo_exists():
                    chat_display.configure(state="normal")
                    chat_display.insert(tk.END, f"Error: {error_msg}\n")
                    chat_display.configure(state="disabled")
                    chat_display.see(tk.END)

            # Check if the message is a move
            elif msg.startswith("{move}"):
                move_text = msg[6:]  # Remove {move} prefix
                process_opponent_move(move_text)

            # Handle regular chat messages
            else:
                if chat_display and chat_display.winfo_exists():
                    chat_display.configure(state="normal")
                    chat_display.insert(tk.END, f"Opponent: {msg}\n")
                    chat_display.configure(state="disabled")
                    chat_display.see(tk.END)

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print("Connection lost.")
            break


def process_opponent_move(move_text):
    """Process an opponent's move from text representation"""
    global board, game_state, chess_canvas

    try:
        # Convert text to chess.Move
        move = chess.Move.from_uci(move_text)

        # Apply the move to our board
        if move in board.legal_moves:
            # Execute the move
            board.push(move)

            # Update game state
            game_state["selected"] = None
            game_state["current_player"] = not game_state["current_player"]
            game_state["my_turn"] = True  # It's now our turn

            # Update the board display if it exists
            if chess_canvas and chess_canvas.winfo_exists():
                # We need to update the board from the main thread
                chess_canvas.after(0, lambda: update_board(chess_canvas, board, game_state))

            # Update status label if it exists
            if status_label and status_label.winfo_exists():
                status_label.config(text="Your turn")

    except Exception as e:
        print(f"Error processing opponent move: {e}")


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


def is_promotion_move(from_square, to_square, board_obj):
    """Check if a move is a pawn promotion move"""
    # Get the piece at the from square
    piece = board_obj.piece_at(from_square)

    # Check if it's a pawn
    if piece and piece.piece_type == chess.PAWN:
        # For white pawns (moving up the board)
        if piece.color == chess.WHITE and chess.square_rank(to_square) == 7:
            return True
        # For black pawns (moving down the board)
        elif piece.color == chess.BLACK and chess.square_rank(to_square) == 0:
            return True

    return False


def show_promotion_ui(canvas, to_square, from_square, color, chess_board, game_state):
    """Show the promotion piece selection UI"""
    # Mark promotion UI as active
    game_state["promotion_ui_active"] = True
    game_state["promotion_move"] = (from_square, to_square)

    # Position of the target square
    rank = 7 - chess.square_rank(to_square)
    file = chess.square_file(to_square)

    # Create a semi-transparent overlay
    canvas.create_rectangle(0, 0, BOARD_SIZE, BOARD_SIZE,
                            fill="gray", stipple="gray50", tags="promotion_overlay")

    # Determine pieces for promotion based on color
    if color:  # White
        promotion_pieces = ['q', 'r', 'b', 'n']  # Queen, Rook, Bishop, Knight
    else:  # Black
        promotion_pieces = ['Q', 'R', 'B', 'N']  # Uppercase for black pieces

    # Create a background for the promotion UI
    bg_width = SQUARE_SIZE
    bg_height = SQUARE_SIZE * 4

    # Position the UI either above or below the promotion square based on color
    if color:  # White (moving upward)
        start_y = max(0, rank * SQUARE_SIZE - bg_height)
    else:  # Black (moving downward)
        start_y = min(BOARD_SIZE - bg_height, (rank + 1) * SQUARE_SIZE)

    canvas.create_rectangle(
        file * SQUARE_SIZE, start_y,
        (file + 1) * SQUARE_SIZE, start_y + bg_height,
        fill="#222222", outline="#555555", width=2,
        tags="promotion_ui"
    )

    # Draw the promotion piece options
    for i, piece in enumerate(promotion_pieces):
        # Draw box for each piece
        piece_y = start_y + i * SQUARE_SIZE
        canvas.create_rectangle(
            file * SQUARE_SIZE, piece_y,
            (file + 1) * SQUARE_SIZE, piece_y + SQUARE_SIZE,
            fill="#333333", outline="#666666",
            tags=f"promotion_option_{piece}"
        )

        # Draw piece image
        canvas.create_image(
            file * SQUARE_SIZE + PIECE_SIZE_TO_SQUARE / 2,
            piece_y + PIECE_SIZE_TO_SQUARE / 2,
            anchor="nw", image=piece_images[piece],
            tags=f"promotion_option_{piece}"
        )

        # Bind click handler to each piece option
        canvas.tag_bind(f"promotion_option_{piece}", "<Button-1>",
                        lambda event, p=piece: handle_promotion_selection(p, canvas, chess_board, game_state))


def handle_promotion_selection(piece, canvas, chess_board, game_state):
    """Handle the selection of a promotion piece"""
    # Clear the promotion UI
    canvas.delete("promotion_ui")
    canvas.delete("promotion_overlay")

    # Get stored move details
    from_square, to_square = game_state["promotion_move"]

    # Create the promotion move with the selected piece
    # Map the FEN piece character to chess.py piece type constants
    piece_type_map = {
        'q': chess.QUEEN, 'r': chess.ROOK, 'b': chess.BISHOP, 'n': chess.KNIGHT,
        'Q': chess.QUEEN, 'R': chess.ROOK, 'B': chess.BISHOP, 'N': chess.KNIGHT
    }

    promotion_piece = piece_type_map[piece]
    move = chess.Move(from_square, to_square, promotion=promotion_piece)

    # Execute the move if legal
    if move in chess_board.legal_moves:
        # Push the move to our local board
        chess_board.push(move)

        # Update game state
        game_state["selected"] = None
        game_state["current_player"] = not game_state["current_player"]
        game_state["my_turn"] = False  # It's opponent's turn now
        game_state["promotion_ui_active"] = False
        game_state["promotion_move"] = None

        # Update status label
        if status_label and status_label.winfo_exists():
            status_label.config(text="Opponent's turn")

        # Send the move to the opponent
        send_message(f"{{move}}{move}")

        # Check for game over
        if chess_board.is_game_over():
            print("Game over!")
            return_to_homescreen = canvas.master.return_to_homescreen if hasattr(canvas.master,
                                                                                 "return_to_homescreen") else None
            if return_to_homescreen:
                canvas.after(2000,
                             lambda: show_game_over_screen(canvas, game_result(chess_board), return_to_homescreen))

    # Update the board display
    update_board(canvas, chess_board, game_state)


def on_square_click(event, canvas, chess_board, game_state, return_to_homescreen):
    """Handle click events on the chess board"""
    # If promotion UI is active, ignore board clicks outside promotion UI
    if game_state["promotion_ui_active"]:
        return

    # Check if my color is assigned yet
    if game_state["my_color"] is None:
        if chat_display and chat_display.winfo_exists():
            chat_display.configure(state="normal")
            chat_display.insert(tk.END, "System: Waiting to be paired with an opponent.\n")
            chat_display.configure(state="disabled")
            chat_display.see(tk.END)
        return

    # Check if it's my turn
    if not game_state["my_turn"]:
        if chat_display and chat_display.winfo_exists():
            chat_display.configure(state="normal")
            chat_display.insert(tk.END, "System: It's not your turn yet.\n")
            chat_display.configure(state="disabled")
            chat_display.see(tk.END)
        return

    # Check if the current player color matches my color (redundant check but keeping for clarity)
    if game_state["current_player"] != game_state["my_color"]:
        return

    row = event.y // SQUARE_SIZE
    col = event.x // SQUARE_SIZE
    square = chess.square(col, 7 - row)
    piece = chess_board.piece_at(square)

    if game_state["selected"]:
        # Check if this is a pawn promotion move
        if is_promotion_move(game_state["selected"], square, chess_board):
            # Show promotion piece selection UI
            show_promotion_ui(canvas, square, game_state["selected"], game_state["my_color"], chess_board, game_state)
            return

        # Regular move
        move = chess.Move(game_state["selected"], square)
        if move in chess_board.legal_moves:
            # Execute the move
            chess_board.push(move)

            # Update game state
            game_state["selected"] = None
            game_state["current_player"] = not game_state["current_player"]
            game_state["my_turn"] = False  # It's now opponent's turn

            # Update status label
            if status_label and status_label.winfo_exists():
                status_label.config(text="Opponent's turn")

            # Send the move to the opponent
            send_message(f"{{move}}{move}")

            # Check for game over
            if chess_board.is_game_over():
                print("Game over!")
                canvas.after(2000,
                             lambda: show_game_over_screen(canvas, game_result(chess_board), return_to_homescreen))
        else:
            # If the move is invalid, but they clicked on their own piece, select that piece instead
            if piece and piece.color == game_state["my_color"]:
                game_state["selected"] = square
            else:
                game_state["selected"] = None
    elif piece and piece.color == game_state["my_color"]:
        game_state["selected"] = square

    update_board(canvas, chess_board, game_state)


def execute_move(move):
    """Execute a chess move and update the game state"""
    global board, game_state

    # Push the move to the board
    board.push(move)

    # Reset selection and change the current player
    game_state["selected"] = None
    game_state["current_player"] = not game_state["current_player"]


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

    # Add visual indicators for the current game state
    # If the game hasn't started yet (no color assigned)
    if game_state["my_color"] is None:
        # Display a "waiting" message on the board
        x_center = BOARD_SIZE / 2
        y_center = BOARD_SIZE / 2
        canvas.create_rectangle(x_center - 150, y_center - 30,
                                x_center + 150, y_center + 30,
                                fill="#333333", outline="#666666", width=2)
        canvas.create_text(x_center, y_center, text="Waiting for opponent...",
                           font=("Arial", 16), fill="white")
        return

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

    # Add visual indicator for whose turn it is
    x_center = BOARD_SIZE / 2
    y_position = BOARD_SIZE - 15


def start_game(window, return_to_homescreen):
    """Start a new chess game"""
    global chat_display, board, game_state, chess_canvas, status_label

    # Reset the game state
    board = chess.Board()
    game_state = {
        "selected": None,
        "current_player": chess.WHITE,
        "my_color": None,  # Will be set when paired
        "my_turn": False,  # Will be set when paired based on color
        "promotion_ui_active": False,
        "promotion_move": None
    }

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

    # Store reference to return_to_homescreen for use in other functions
    chess_canvas.master.return_to_homescreen = return_to_homescreen

    # Add status label
    status_label = tk.Label(canvas, text="Waiting for game to start...",
                            font=("Arial", 14), bg="white", relief="ridge", padx=10, pady=5)
    canvas.create_window(window.winfo_screenwidth() / 2,
                         window.winfo_screenheight() / 2 - BOARD_SIZE / 2 - 30,
                         window=status_label)

    # Load images and draw board
    load_images()

    draw_board(chess_canvas)
    draw_pieces(chess_canvas)

    # Bind clicks
    chess_canvas.bind("<Button-1>",
                      lambda event: on_square_click(event, chess_canvas, board, game_state, return_to_homescreen))

    # === Create Buttons (Draw, Resign) ===
    draw_button = tk.Button(canvas, text="Offer Draw", width=15)
    resign_button = tk.Button(canvas, text="Resign", width=15, command=lambda: resign_game(return_to_homescreen))

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


def resign_game(return_to_homescreen):
    """Resign the current game"""
    send_message("{quit_game}")
    return_to_homescreen()


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