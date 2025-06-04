import tkinter as tk
import tkinter.messagebox
from PIL import Image, ImageTk
import chess
from threading import Thread
import time
import os
from SQLL_database import UserDatabase
from chess_bot import minimax  # Import the minimax function from your chess bot

# Constants
BOARD_SIZE = 800
SQUARE_SIZE = BOARD_SIZE // 8
PIECE_SIZE_TO_SQUARE = 15
COLORS = {'odd': '#83CB72', 'even': '#DCE2D6'}
CIRCLE_CONST = 35

# Global variables
piece_images = {}
chess_bot_board = chess.Board()
chess_bot_game_state = {
    "selected": None,
    "current_player": chess.WHITE,
    "my_color": chess.WHITE,
    "my_turn": True,
    "game_active": True
}

chess_bot_canvas = None
chess_bot_status_label = None
chess_bot_difficulty = 3  # Default depth for minimax
chess_bot_player_name = "Player1"


def load_piece_images():
    """Load chess piece images"""
    global piece_images
    piece_names = {
        'R': "white rook", 'N': "white knight", 'B': "white bishop",
        'Q': "white queen", 'K': "white king", 'P': "white pawn",
        'r': "black rook", 'n': "black knight", 'b': "black bishop",
        'q': "black queen", 'k': "black king", 'p': "black pawn",
    }

    for key, name in piece_names.items():
        try:
            img = Image.open(f"assets/pieces/{name}.png")
            img = img.resize((SQUARE_SIZE - PIECE_SIZE_TO_SQUARE, SQUARE_SIZE - PIECE_SIZE_TO_SQUARE))
            piece_images[key] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading {name}.png: {e}")


def draw_board(canvas):
    """Draw the chess board squares"""
    for row in range(8):
        for col in range(8):
            color = COLORS['odd'] if (row + col) % 2 == 0 else COLORS['even']
            canvas.create_rectangle(col * SQUARE_SIZE, row * SQUARE_SIZE,
                                    (col + 1) * SQUARE_SIZE, (row + 1) * SQUARE_SIZE,
                                    fill=color, outline="")


def draw_pieces(canvas, fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
    """Draw chess pieces on the board based on FEN notation"""
    board_fen = fen.split()[0].replace('/', '')
    i = 0
    for piece_fen in board_fen:
        if piece_fen.isdigit():
            i += int(piece_fen)
        else:
            if piece_fen in piece_images:
                canvas.create_image((i % 8) * SQUARE_SIZE + PIECE_SIZE_TO_SQUARE / 2,
                                    (i // 8) * SQUARE_SIZE + PIECE_SIZE_TO_SQUARE / 2,
                                    anchor="nw", image=piece_images[piece_fen])
            i += 1


def chess_bot_make_move():
    """Make chess bot move using the minimax algorithm"""
    global chess_bot_board, chess_bot_game_state

    if not chess_bot_game_state["game_active"] or chess_bot_game_state["my_turn"]:
        return

    try:
        # Use minimax to get the best move
        # The bot plays as black (maximizing_color = chess.BLACK)
        best_move, _ = minimax(chess_bot_board, chess_bot_difficulty, True, chess.BLACK)

        if best_move and best_move in chess_bot_board.legal_moves:
            chess_bot_board.push(best_move)
            chess_bot_game_state["selected"] = None
            chess_bot_game_state["current_player"] = chess.WHITE
            chess_bot_game_state["my_turn"] = True

            if chess_bot_canvas and chess_bot_canvas.winfo_exists():
                chess_bot_canvas.after(0, update_board)

            if chess_bot_status_label and chess_bot_status_label.winfo_exists():
                chess_bot_canvas.after(0, lambda: chess_bot_status_label.config(text="Your turn"))

            if chess_bot_board.is_game_over():
                result_text = get_game_result()
                chess_bot_game_state["game_active"] = False

                return_to_homescreen = getattr(chess_bot_canvas.master, 'return_to_homescreen', None)
                if return_to_homescreen:
                    chess_bot_canvas.after(1000, lambda: show_game_over(result_text, return_to_homescreen))
        else:
            print("Chess bot returned no valid move")

    except Exception as e:
        print(f"Chess bot move error: {e}")
        # Try to continue the game even if the bot fails
        if chess_bot_canvas and chess_bot_canvas.winfo_exists():
            chess_bot_canvas.after(0, lambda: chess_bot_status_label.config(text="Bot error - Your turn"))


def get_game_result():
    """Get game result text"""
    if chess_bot_board.result() == "1-0":
        return "White wins!"
    elif chess_bot_board.result() == "0-1":
        return "Black wins!"
    else:
        return "Draw!"


def on_square_click(event):
    """Handle square clicks"""
    global chess_bot_board, chess_bot_game_state

    if not chess_bot_game_state["game_active"] or not chess_bot_game_state["my_turn"]:
        return

    row = event.y // SQUARE_SIZE
    col = event.x // SQUARE_SIZE

    print(row, col)

    # Use chess.square with correct rank calculation
    square = chess.square(col, 7 - row)

    print(square)
    piece = chess_bot_board.piece_at(square)
    print(piece)

    if chess_bot_game_state["selected"] is not None:
        move = chess.Move(chess_bot_game_state["selected"], square)
        if move in chess_bot_board.legal_moves:
            chess_bot_board.push(move)
            chess_bot_game_state["selected"] = None
            chess_bot_game_state["current_player"] = chess.BLACK
            chess_bot_game_state["my_turn"] = False

            if chess_bot_status_label:
                chess_bot_status_label.config(text="Bot thinking...")

            if chess_bot_board.is_game_over():
                result_text = get_game_result()
                chess_bot_game_state["game_active"] = False

                return_to_homescreen = getattr(chess_bot_canvas.master, 'return_to_homescreen', None)
                if return_to_homescreen:
                    chess_bot_canvas.after(1000, lambda: show_game_over(result_text, return_to_homescreen))
                return

            Thread(target=chess_bot_make_move, daemon=True).start()
        else:
            if piece and piece.color == chess.WHITE:
                chess_bot_game_state["selected"] = square
            else:
                chess_bot_game_state["selected"] = None
    elif piece and piece.color == chess.WHITE:
        chess_bot_game_state["selected"] = square

    update_board()


def update_board():
    """Update the board display"""
    if not chess_bot_canvas or not chess_bot_canvas.winfo_exists():
        return

    chess_bot_canvas.delete("all")
    draw_board(chess_bot_canvas)
    draw_pieces(chess_bot_canvas, chess_bot_board.fen())

    # Highlight selected square
    if chess_bot_game_state["selected"] is not None:
        row = 7 - chess.square_rank(chess_bot_game_state["selected"])
        col = chess.square_file(chess_bot_game_state["selected"])
        x1, y1 = col * SQUARE_SIZE, row * SQUARE_SIZE
        x2, y2 = x1 + SQUARE_SIZE, y1 + SQUARE_SIZE
        chess_bot_canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3)

        # Show possible moves
        for move in chess_bot_board.legal_moves:
            if move.from_square == chess_bot_game_state["selected"]:
                move_row = 7 - chess.square_rank(move.to_square)
                move_col = chess.square_file(move.to_square)
                x1 = move_col * SQUARE_SIZE + CIRCLE_CONST
                y1 = move_row * SQUARE_SIZE + CIRCLE_CONST
                x2 = x1 + SQUARE_SIZE - 2 * CIRCLE_CONST
                y2 = y1 + SQUARE_SIZE - 2 * CIRCLE_CONST
                chess_bot_canvas.create_oval(x1, y1, x2, y2, fill="gray")


def show_difficulty_selection(window, return_to_homescreen):
    """Show difficulty selection dialog"""
    global chess_bot_difficulty

    overlay = tk.Frame(window, bg="black")
    overlay.place(x=0, y=0, relwidth=1, relheight=1)

    # Main frame
    main_frame = tk.Frame(overlay, bg="#222222", relief="ridge", bd=3)
    main_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=500)

    tk.Label(main_frame, text="Select Bot Difficulty", font=("Arial", 20, "bold"),
             bg="#222222", fg="white").pack(pady=20)

    difficulties = [
        ("Very Easy", 1), ("Easy", 2), ("Medium", 3),
        ("Hard", 4), ("Very Hard", 5), ("Expert", 6)
    ]

    selected = tk.IntVar(value=chess_bot_difficulty)

    for name, level in difficulties:
        tk.Radiobutton(main_frame, text=f"{name} (Depth {level})",
                       variable=selected, value=level, font=("Arial", 12),
                       bg="#222222", fg="white", selectcolor="#444444").pack(pady=5)

    def start_game():
        global chess_bot_difficulty
        chess_bot_difficulty = selected.get()
        overlay.destroy()
        start_chess_bot_game(window, return_to_homescreen)

    tk.Button(main_frame, text="Start Game", command=start_game,
              font=("Arial", 12), bg="green", fg="white", width=15).pack(pady=10)
    tk.Button(main_frame, text="Cancel", command=overlay.destroy,
              font=("Arial", 12), bg="red", fg="white", width=15).pack(pady=5)


def start_chess_bot_game(window, return_to_homescreen):
    """Start the chess bot game"""
    global chess_bot_board, chess_bot_game_state, chess_bot_canvas, chess_bot_status_label

    # Reset game
    chess_bot_board = chess.Board()
    chess_bot_game_state = {
        "selected": None, "current_player": chess.WHITE,
        "my_color": chess.WHITE, "my_turn": True, "game_active": True
    }

    # Clear window
    for widget in window.winfo_children():
        widget.pack_forget()
        widget.place_forget()

    # Create game interface
    bg_frame = tk.Frame(window)
    bg_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(bg_frame)
    canvas.pack(fill="both", expand=True)

    # Background
    try:
        bg_image = ImageTk.PhotoImage(
            Image.open("assets/utils/chessBackground.jpg").resize(
                (window.winfo_screenwidth(), window.winfo_screenheight())))
        canvas.bg_image = bg_image
        canvas.create_image(0, 0, image=bg_image, anchor=tk.NW)
    except:
        canvas.configure(bg="darkgreen")

    # Chess board
    chess_bot_canvas = tk.Canvas(canvas, width=BOARD_SIZE, height=BOARD_SIZE,
                                 bd=5, relief="ridge", bg="white")
    chess_bot_canvas.place(relx=0.5, rely=0.5, anchor="center")
    chess_bot_canvas.master.return_to_homescreen = return_to_homescreen

    # Status
    chess_bot_status_label = tk.Label(canvas, text="Your turn - You are White",
                                      font=("Arial", 14), bg="white", relief="ridge")
    canvas.create_window(window.winfo_screenwidth() / 2,
                         window.winfo_screenheight() / 2 - BOARD_SIZE / 2 - 40,
                         window=chess_bot_status_label)

    # Load and draw
    load_piece_images()
    update_board()

    # Bind events
    chess_bot_canvas.bind("<Button-1>", on_square_click)

    # Resign button
    resign_btn = tk.Button(canvas, text="Resign", font=("Arial", 12),
                           command=lambda: resign_game(return_to_homescreen))
    canvas.create_window(window.winfo_screenwidth() / 2,
                         window.winfo_screenheight() / 2 + BOARD_SIZE / 2 + 30,
                         window=resign_btn)


def resign_game(return_to_homescreen):
    """Resign the game"""
    global chess_bot_game_state
    chess_bot_game_state["game_active"] = False
    show_game_over("You resigned! Bot wins.", return_to_homescreen)


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


def show_game_over(result_text, return_to_homescreen):
    """Show game over screen with modern design"""
    global chess_bot_player_name

    # Show result with modern design
    if chess_bot_canvas and chess_bot_canvas.winfo_exists():
        # Get canvas dimensions
        canvas_width = chess_bot_canvas.winfo_width()
        canvas_height = chess_bot_canvas.winfo_height()

        # Center coordinates
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        rect_width = 300
        rect_height = 200

        # Clear the canvas
        chess_bot_canvas.delete("all")

        # Draw a semi-transparent dark background
        chess_bot_canvas.create_rectangle(0, 0, canvas_width, canvas_height,
                                          fill="#000000", stipple="gray50", outline="")

        # Draw rounded rectangle background
        create_rounded_rectangle(
            chess_bot_canvas,
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
        chess_bot_canvas.create_text(center_x, center_y - rect_height / 4,
                                     text=result_text, font=("Arial", 24, "bold"), fill="white")

        # Create "Return Home" button
        return_btn = tk.Button(chess_bot_canvas, text="Return Home",
                               font=("Arial", 14), command=return_to_homescreen)
        chess_bot_canvas.create_window(center_x, center_y + rect_height / 4, window=return_btn)


def play_with_chess_bot(window, return_to_homescreen, player_name="Player1"):
    """Main entry point"""
    global chess_bot_player_name
    chess_bot_player_name = player_name
    show_difficulty_selection(window, return_to_homescreen)