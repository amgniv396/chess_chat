import tkinter as tk
import tkinter.messagebox
from PIL import Image, ImageTk
import chess
from stockfish import Stockfish
from threading import Thread
import time
import os
from SQLL_database import UserDatabase

# Constants
BOARD_SIZE = 800
SQUARE_SIZE = BOARD_SIZE // 8
PIECE_SIZE_TO_SQUARE = 15
COLORS = {'odd': '#83CB72', 'even': '#DCE2D6'}
CIRCLE_CONST = 35

# Global variables
piece_images = {}
stockfish_board = chess.Board()
stockfish_game_state = {
    "selected": None,
    "current_player": chess.WHITE,
    "my_color": chess.WHITE,
    "my_turn": True,
    "game_active": True
}

stockfish_engine = None
stockfish_canvas = None
stockfish_status_label = None
stockfish_difficulty = 1
stockfish_player_name = "Player1"


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


def initialize_stockfish_engine(difficulty=1):
    """Initialize the Stockfish engine using the stockfish library"""
    global stockfish_engine

    try:
        # Clean up any existing engine first
        if stockfish_engine is not None:
            try:
                del stockfish_engine
            except:
                pass
            stockfish_engine = None

        # Try to create Stockfish engine without specifying path first
        try:
            stockfish_engine = Stockfish()
            # Test if it works
            test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            if not stockfish_engine.is_fen_valid(test_fen):
                raise Exception("Stockfish validation failed")
        except Exception as e:
            print(f"Default Stockfish failed: {e}, trying specific paths...")

            # Try specific paths
            stockfish_paths = [
                "stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe"
            ]

            stockfish_engine = None
            for path in stockfish_paths:
                if os.path.exists(path):
                    try:
                        stockfish_engine = Stockfish(path=path)
                        test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                        if stockfish_engine.is_fen_valid(test_fen):
                            print(f"Stockfish initialized with path: {path}")
                            break
                        else:
                            del stockfish_engine
                            stockfish_engine = None
                    except Exception as path_error:
                        print(f"Failed with path {path}: {path_error}")
                        if stockfish_engine:
                            try:
                                del stockfish_engine
                            except:
                                pass
                            stockfish_engine = None
                        continue

            if stockfish_engine is None:
                raise FileNotFoundError("Could not initialize Stockfish with any available path")

        # Configure engine strength based on difficulty
        try:
            if difficulty <= 5:
                # Beginner levels
                stockfish_engine.set_depth(max(1, difficulty))
                if hasattr(stockfish_engine, 'set_elo_rating'):
                    stockfish_engine.set_elo_rating(800 + (difficulty - 1) * 100)
            elif difficulty <= 10:
                # Intermediate levels
                stockfish_engine.set_depth(5 + (difficulty - 5))
                if hasattr(stockfish_engine, 'set_elo_rating'):
                    stockfish_engine.set_elo_rating(1200 + (difficulty - 6) * 150)
            elif difficulty <= 15:
                # Advanced levels
                stockfish_engine.set_depth(10 + (difficulty - 10))
                if hasattr(stockfish_engine, 'set_elo_rating'):
                    stockfish_engine.set_elo_rating(1950 + (difficulty - 11) * 100)
            else:
                # Expert levels - full strength
                stockfish_engine.set_depth(15)
        except Exception as config_error:
            print(f"Warning: Could not configure engine settings: {config_error}")
            # Continue anyway with default settings

        print(f"Stockfish initialized successfully for difficulty level {difficulty}")
        return True

    except Exception as e:
        print(f"Failed to initialize Stockfish: {e}")
        if stockfish_engine:
            try:
                del stockfish_engine
            except:
                pass
            stockfish_engine = None
        return False


def stockfish_make_move():
    """Make Stockfish move using the stockfish library"""
    global stockfish_board, stockfish_game_state, stockfish_engine

    if not stockfish_game_state["game_active"] or stockfish_game_state["my_turn"] or stockfish_engine is None:
        return

    try:
        # Set the current position in Stockfish
        current_fen = stockfish_board.fen()
        stockfish_engine.set_fen_position(current_fen)

        # Get best move from Stockfish
        best_move = stockfish_engine.get_best_move()

        if best_move:
            # Convert to chess.Move object
            move = chess.Move.from_uci(best_move)

            if move in stockfish_board.legal_moves:
                stockfish_board.push(move)
                stockfish_game_state["selected"] = None
                stockfish_game_state["current_player"] = chess.WHITE
                stockfish_game_state["my_turn"] = True

                if stockfish_canvas and stockfish_canvas.winfo_exists():
                    stockfish_canvas.after(0, update_board)

                if stockfish_status_label and stockfish_status_label.winfo_exists():
                    stockfish_canvas.after(0, lambda: stockfish_status_label.config(text="Your turn"))

                if stockfish_board.is_game_over():
                    result_text = get_game_result()
                    win = "White" in result_text
                    stockfish_game_state["game_active"] = False

                    return_to_homescreen = getattr(stockfish_canvas.master, 'return_to_homescreen', None)
                    if return_to_homescreen:
                        stockfish_canvas.after(1000, lambda: show_game_over(result_text, return_to_homescreen))
            else:
                print(f"Stockfish suggested illegal move: {best_move}")
        else:
            print("Stockfish returned no move")

    except Exception as e:
        print(f"Stockfish move error: {e}")
        # Try to continue the game even if Stockfish fails
        if stockfish_canvas and stockfish_canvas.winfo_exists():
            stockfish_canvas.after(0, lambda: stockfish_status_label.config(text="Stockfish error - Your turn"))


def get_game_result():
    """Get game result text"""
    if stockfish_board.result() == "1-0":
        return "White wins!"
    elif stockfish_board.result() == "0-1":
        return "Black wins!"
    else:
        return "Draw!"


def on_square_click(event):
    """Handle square clicks"""
    global stockfish_board, stockfish_game_state

    if not stockfish_game_state["game_active"] or not stockfish_game_state["my_turn"]:
        return

    row = event.y // SQUARE_SIZE
    col = event.x // SQUARE_SIZE

    print(row,col)

    # FIX: Use chess.square with correct rank calculation
    square = chess.square(col, 7 - row)  # This was the bug - row needs to be flipped

    print(square)
    piece = stockfish_board.piece_at(square)
    print(piece)
    if stockfish_game_state["selected"] is not None:
        move = chess.Move(stockfish_game_state["selected"], square)
        if move in stockfish_board.legal_moves:
            stockfish_board.push(move)
            stockfish_game_state["selected"] = None
            stockfish_game_state["current_player"] = chess.BLACK
            stockfish_game_state["my_turn"] = False

            if stockfish_status_label:
                stockfish_status_label.config(text="Stockfish thinking...")

            if stockfish_board.is_game_over():
                result_text = get_game_result()
                win = "White" in result_text
                stockfish_game_state["game_active"] = False

                return_to_homescreen = getattr(stockfish_canvas.master, 'return_to_homescreen', None)
                if return_to_homescreen:
                    stockfish_canvas.after(1000, lambda: show_game_over(result_text, return_to_homescreen))
                return

            Thread(target=stockfish_make_move, daemon=True).start()
        else:
            if piece and piece.color == chess.WHITE:
                stockfish_game_state["selected"] = square
            else:
                stockfish_game_state["selected"] = None
    elif piece and piece.color == chess.WHITE:
        stockfish_game_state["selected"] = square

    update_board()


def update_board():
    """Update the board display"""
    if not stockfish_canvas or not stockfish_canvas.winfo_exists():
        return

    stockfish_canvas.delete("all")
    draw_board(stockfish_canvas)
    draw_pieces(stockfish_canvas, stockfish_board.fen())

    # Highlight selected square
    if stockfish_game_state["selected"] is not None:
        row = 7 - chess.square_rank(stockfish_game_state["selected"])
        col = chess.square_file(stockfish_game_state["selected"])
        x1, y1 = col * SQUARE_SIZE, row * SQUARE_SIZE
        x2, y2 = x1 + SQUARE_SIZE, y1 + SQUARE_SIZE
        stockfish_canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3)

        # Show possible moves
        for move in stockfish_board.legal_moves:
            if move.from_square == stockfish_game_state["selected"]:
                move_row = 7 - chess.square_rank(move.to_square)
                move_col = chess.square_file(move.to_square)
                x1 = move_col * SQUARE_SIZE + CIRCLE_CONST
                y1 = move_row * SQUARE_SIZE + CIRCLE_CONST
                x2 = x1 + SQUARE_SIZE - 2 * CIRCLE_CONST
                y2 = y1 + SQUARE_SIZE - 2 * CIRCLE_CONST
                stockfish_canvas.create_oval(x1, y1, x2, y2, fill="gray")


def show_difficulty_selection(window, return_to_homescreen):
    """Show difficulty selection dialog"""
    global stockfish_difficulty

    overlay = tk.Frame(window, bg="black")
    overlay.place(x=0, y=0, relwidth=1, relheight=1)

    # Main frame
    main_frame = tk.Frame(overlay, bg="#222222", relief="ridge", bd=3)
    main_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=500)

    tk.Label(main_frame, text="Select Difficulty", font=("Arial", 20, "bold"),
             bg="#222222", fg="white").pack(pady=20)

    difficulties = [
        ("Beginner", 1), ("Easy", 3), ("Medium", 7),
        ("Hard", 12), ("Expert", 18), ("Master", 20)
    ]

    selected = tk.IntVar(value=stockfish_difficulty)

    for name, level in difficulties:
        tk.Radiobutton(main_frame, text=f"{name} (Level {level})",
                       variable=selected, value=level, font=("Arial", 12),
                       bg="#222222", fg="white", selectcolor="#444444").pack(pady=5)

    def start_game():
        global stockfish_difficulty
        stockfish_difficulty = selected.get()
        overlay.destroy()
        start_stockfish_game(window, return_to_homescreen)

    tk.Button(main_frame, text="Start Game", command=start_game,
              font=("Arial", 12), bg="green", fg="white", width=15).pack(pady=10)
    tk.Button(main_frame, text="Cancel", command=overlay.destroy,
              font=("Arial", 12), bg="red", fg="white", width=15).pack(pady=5)


def start_stockfish_game(window, return_to_homescreen):
    """Start the Stockfish game"""
    global stockfish_board, stockfish_game_state, stockfish_canvas, stockfish_status_label

    if not initialize_stockfish_engine(stockfish_difficulty):
        tkinter.messagebox.showerror("Error", "Failed to initialize Stockfish!\nMake sure Stockfish is installed.")
        return

    # Reset game
    stockfish_board = chess.Board()
    stockfish_game_state = {
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
    stockfish_canvas = tk.Canvas(canvas, width=BOARD_SIZE, height=BOARD_SIZE,
                                 bd=5, relief="ridge", bg="white")
    stockfish_canvas.place(relx=0.5, rely=0.5, anchor="center")
    stockfish_canvas.master.return_to_homescreen = return_to_homescreen

    # Status
    stockfish_status_label = tk.Label(canvas, text="Your turn - You are White",
                                      font=("Arial", 14), bg="white", relief="ridge")
    canvas.create_window(window.winfo_screenwidth() / 2,
                         window.winfo_screenheight() / 2 - BOARD_SIZE / 2 - 40,
                         window=stockfish_status_label)

    # Load and draw
    load_piece_images()
    update_board()

    # Bind events
    stockfish_canvas.bind("<Button-1>", on_square_click)

    # Resign button
    resign_btn = tk.Button(canvas, text="Resign", font=("Arial", 12),
                           command=lambda: resign_game(return_to_homescreen))
    canvas.create_window(window.winfo_screenwidth() / 2,
                         window.winfo_screenheight() / 2 + BOARD_SIZE / 2 + 30,
                         window=resign_btn)


def cleanup_stockfish():
    """Clean up Stockfish engine safely"""
    global stockfish_engine

    if stockfish_engine is not None:
        try:
            # The stockfish library should handle cleanup automatically
            del stockfish_engine
        except Exception as e:
            print(f"Error during Stockfish cleanup: {e}")
        finally:
            stockfish_engine = None


def resign_game(return_to_homescreen):
    """Resign the game"""
    global stockfish_game_state
    stockfish_game_state["game_active"] = False
    cleanup_stockfish()
    show_game_over("You resigned! Stockfish wins.", return_to_homescreen)


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
    """Show game over screen with modern design like chess_client_graphics"""
    global stockfish_player_name

    # Clean up Stockfish engine
    cleanup_stockfish()

    # Show result with modern design
    if stockfish_canvas and stockfish_canvas.winfo_exists():
        # Get canvas dimensions
        canvas_width = stockfish_canvas.winfo_width()
        canvas_height = stockfish_canvas.winfo_height()

        # Center coordinates
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        rect_width = 300
        rect_height = 200

        # Clear the canvas
        stockfish_canvas.delete("all")

        # Draw a semi-transparent dark background
        stockfish_canvas.create_rectangle(0, 0, canvas_width, canvas_height,
                                          fill="#000000", stipple="gray50", outline="")

        # Draw rounded rectangle background
        create_rounded_rectangle(
            stockfish_canvas,
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
        stockfish_canvas.create_text(center_x, center_y - rect_height / 4,
                                     text=result_text, font=("Arial", 24, "bold"), fill="white")

        # Create "Return Home" button
        return_btn = tk.Button(stockfish_canvas, text="Return Home",
                               font=("Arial", 14), command=return_to_homescreen)
        stockfish_canvas.create_window(center_x, center_y + rect_height / 4, window=return_btn)


def play_with_stockfish(window, return_to_homescreen, player_name="Player1"):
    """Main entry point"""
    global stockfish_player_name
    stockfish_player_name = player_name
    show_difficulty_selection(window, return_to_homescreen)