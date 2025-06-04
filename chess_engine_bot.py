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
BOARD_SIZE = 760  # Using the larger size from stockfish version
SQUARE_SIZE = BOARD_SIZE // 8
PIECE_SIZE_TO_SQUARE = 15
COLORS = {'odd': '#83CB72', 'even': '#DCE2D6'}
CIRCLE_CONST = 35

# Global variables - shared by both engines
piece_images = {}
game_board = chess.Board()
game_state = {
    "selected": None,
    "current_player": chess.WHITE,
    "my_color": chess.WHITE,
    "my_turn": True,
    "game_active": True
}

game_canvas = None
status_label = None
difficulty = 1
player_name = "Player1"

# Engine-specific globals
stockfish_engine = None
chess_bot_instance = None


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


def get_game_result():
    """Get game result text from player's perspective"""
    if game_board.result() == "1-0":
        # White wins - since player is always white, player wins
        return "You won!"
    elif game_board.result() == "0-1":
        # Black wins - since player is always white, player loses
        return "You lost!"
    else:
        # Draw
        return "Draw!"


def on_square_click(event, engine_type):
    """Handle square clicks - unified for both engines"""
    global game_board, game_state

    if not game_state["game_active"] or not game_state["my_turn"]:
        return

    row = event.y // SQUARE_SIZE
    col = event.x // SQUARE_SIZE

    print(row, col)

    # Use chess.square with correct rank calculation
    square = chess.square(col, 7 - row)

    print(square)
    piece = game_board.piece_at(square)
    print(piece)

    if game_state["selected"] is not None:
        move = chess.Move(game_state["selected"], square)
        if move in game_board.legal_moves:
            game_board.push(move)
            game_state["selected"] = None
            game_state["current_player"] = chess.BLACK
            game_state["my_turn"] = False

            if status_label:
                if engine_type == "stockfish":
                    status_label.config(text="Stockfish thinking...")
                else:
                    status_label.config(text="Bot thinking...")

            if game_board.is_game_over():
                result_text = get_game_result()
                game_state["game_active"] = False

                return_to_homescreen = getattr(game_canvas.master, 'return_to_homescreen', None)
                if return_to_homescreen:
                    game_canvas.after(1000, lambda: show_game_over(result_text, return_to_homescreen))
                return

            # Start the appropriate engine move
            if engine_type == "stockfish":
                Thread(target=stockfish_make_move, daemon=True).start()
            else:
                Thread(target=chess_bot_make_move, daemon=True).start()
        else:
            if piece and piece.color == chess.WHITE:
                game_state["selected"] = square
            else:
                game_state["selected"] = None
    elif piece and piece.color == chess.WHITE:
        game_state["selected"] = square

    update_board()


def update_board():
    """Update the board display"""
    if not game_canvas or not game_canvas.winfo_exists():
        return

    game_canvas.delete("all")
    draw_board(game_canvas)
    draw_pieces(game_canvas, game_board.fen())

    # Highlight selected square
    if game_state["selected"] is not None:
        row = 7 - chess.square_rank(game_state["selected"])
        col = chess.square_file(game_state["selected"])
        x1, y1 = col * SQUARE_SIZE, row * SQUARE_SIZE
        x2, y2 = x1 + SQUARE_SIZE, y1 + SQUARE_SIZE
        game_canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3)

        # Show possible moves
        for move in game_board.legal_moves:
            if move.from_square == game_state["selected"]:
                move_row = 7 - chess.square_rank(move.to_square)
                move_col = chess.square_file(move.to_square)
                x1 = move_col * SQUARE_SIZE + CIRCLE_CONST
                y1 = move_row * SQUARE_SIZE + CIRCLE_CONST
                x2 = x1 + SQUARE_SIZE - 2 * CIRCLE_CONST
                y2 = y1 + SQUARE_SIZE - 2 * CIRCLE_CONST
                game_canvas.create_oval(x1, y1, x2, y2, fill="gray")


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
    global player_name

    # Show result with modern design
    if game_canvas and game_canvas.winfo_exists():
        # Get canvas dimensions
        canvas_width = game_canvas.winfo_width()
        canvas_height = game_canvas.winfo_height()

        # Center coordinates
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        rect_width = 300
        rect_height = 200

        # Clear the canvas
        game_canvas.delete("all")

        # Draw a semi-transparent dark background
        game_canvas.create_rectangle(0, 0, canvas_width, canvas_height,
                                     fill="#000000", stipple="gray50", outline="")

        # Draw rounded rectangle background
        create_rounded_rectangle(
            game_canvas,
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
        game_canvas.create_text(center_x, center_y - rect_height / 4,
                                text=result_text, font=("Arial", 24, "bold"), fill="white")

        # Create "Return Home" button
        return_btn = tk.Button(game_canvas, text="Return Home",
                               font=("Arial", 14), command=return_to_homescreen)
        game_canvas.create_window(center_x, center_y + rect_height / 4, window=return_btn)


def create_game_interface(window, return_to_homescreen, engine_type):
    """Create the unified game interface"""
    global game_canvas, status_label

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
    game_canvas = tk.Canvas(canvas, width=BOARD_SIZE, height=BOARD_SIZE,
                            bd=5, relief="ridge", bg="white")
    game_canvas.place(relx=0.5, rely=0.5, anchor="center")
    game_canvas.master.return_to_homescreen = return_to_homescreen

    # Status label with engine-specific text
    if engine_type == "stockfish":
        status_text = "Your turn - You are White"
    else:
        difficulty_names = {2: "Beginner", 3: "Easy", 4: "Medium", 5: "Hard"}
        difficulty_name = difficulty_names.get(difficulty, "Unknown")
        status_text = f"Your turn - You are White (vs {difficulty_name} Bot)"

    status_label = tk.Label(canvas, text=status_text,
                            font=("Arial", 14), bg="white", relief="ridge")
    canvas.create_window(window.winfo_screenwidth() / 2,
                         window.winfo_screenheight() / 2 - BOARD_SIZE / 2 - 40,
                         window=status_label)

    # Load and draw
    load_piece_images()
    update_board()

    # Bind events with engine type
    game_canvas.bind("<Button-1>", lambda event: on_square_click(event, engine_type))

    # Resign button
    resign_btn = tk.Button(canvas, text="Resign", font=("Arial", 12),
                           command=lambda: resign_game(return_to_homescreen, engine_type))
    canvas.create_window(window.winfo_screenwidth() / 2,
                         window.winfo_screenheight() / 2 + BOARD_SIZE / 2 + 30,
                         window=resign_btn)


def resign_game(return_to_homescreen, engine_type):
    """Resign the game"""
    global game_state
    game_state["game_active"] = False

    if engine_type == "stockfish":
        cleanup_stockfish()
        show_game_over("You resigned!\nYou lost!", return_to_homescreen)
    else:
        show_game_over("You resigned!\nYou lost!", return_to_homescreen)


# ============= STOCKFISH-SPECIFIC FUNCTIONS =============

def initialize_stockfish_engine(difficulty_level=1):
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
            if difficulty_level <= 5:
                # Beginner levels
                stockfish_engine.set_depth(max(1, difficulty_level))
                if hasattr(stockfish_engine, 'set_elo_rating'):
                    stockfish_engine.set_elo_rating(800 + (difficulty_level - 1) * 100)
            elif difficulty_level <= 10:
                # Intermediate levels
                stockfish_engine.set_depth(5 + (difficulty_level - 5))
                if hasattr(stockfish_engine, 'set_elo_rating'):
                    stockfish_engine.set_elo_rating(1200 + (difficulty_level - 6) * 150)
            elif difficulty_level <= 15:
                # Advanced levels
                stockfish_engine.set_depth(10 + (difficulty_level - 10))
                if hasattr(stockfish_engine, 'set_elo_rating'):
                    stockfish_engine.set_elo_rating(1950 + (difficulty_level - 11) * 100)
            else:
                # Expert levels - full strength
                stockfish_engine.set_depth(15)
        except Exception as config_error:
            print(f"Warning: Could not configure engine settings: {config_error}")
            # Continue anyway with default settings

        print(f"Stockfish initialized successfully for difficulty level {difficulty_level}")
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
    global game_board, game_state, stockfish_engine

    if not game_state["game_active"] or game_state["my_turn"] or stockfish_engine is None:
        return

    try:
        # Set the current position in Stockfish
        current_fen = game_board.fen()
        stockfish_engine.set_fen_position(current_fen)

        # Get best move from Stockfish
        best_move = stockfish_engine.get_best_move()

        if best_move:
            # Convert to chess.Move object
            move = chess.Move.from_uci(best_move)

            if move in game_board.legal_moves:
                game_board.push(move)
                game_state["selected"] = None
                game_state["current_player"] = chess.WHITE
                game_state["my_turn"] = True

                if game_canvas and game_canvas.winfo_exists():
                    game_canvas.after(0, update_board)

                if status_label and status_label.winfo_exists():
                    game_canvas.after(0, lambda: status_label.config(text="Your turn"))

                if game_board.is_game_over():
                    result_text = get_game_result()
                    game_state["game_active"] = False

                    return_to_homescreen = getattr(game_canvas.master, 'return_to_homescreen', None)
                    if return_to_homescreen:
                        game_canvas.after(1000, lambda: show_game_over(result_text, return_to_homescreen))
            else:
                print(f"Stockfish suggested illegal move: {best_move}")
        else:
            print("Stockfish returned no move")

    except Exception as e:
        print(f"Stockfish move error: {e}")
        # Try to continue the game even if Stockfish fails
        if game_canvas and game_canvas.winfo_exists():
            game_canvas.after(0, lambda: status_label.config(text="Stockfish error - Your turn"))


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


def show_stockfish_difficulty_selection(window, return_to_homescreen):
    """Show difficulty selection dialog for Stockfish"""
    global difficulty

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

    selected = tk.IntVar(value=1)

    for name, level in difficulties:
        tk.Radiobutton(main_frame, text=f"{name} (Level {level})",
                       variable=selected, value=level, font=("Arial", 12),
                       bg="#222222", fg="white", selectcolor="#444444").pack(pady=5)

    def start_game():
        global difficulty
        difficulty = selected.get()
        overlay.destroy()
        start_stockfish_game(window, return_to_homescreen)

    tk.Button(main_frame, text="Start Game", command=start_game,
              font=("Arial", 12), bg="green", fg="white", width=15).pack(pady=10)
    tk.Button(main_frame, text="Cancel", command=overlay.destroy,
              font=("Arial", 12), bg="red", fg="white", width=15).pack(pady=5)


def start_stockfish_game(window, return_to_homescreen):
    """Start the Stockfish game"""
    global game_board, game_state

    if not initialize_stockfish_engine(difficulty):
        tkinter.messagebox.showerror("Error", "Failed to initialize Stockfish!\nMake sure Stockfish is installed.")
        return

    # Reset game
    game_board = chess.Board()
    game_state = {
        "selected": None, "current_player": chess.WHITE,
        "my_color": chess.WHITE, "my_turn": True, "game_active": True
    }

    create_game_interface(window, return_to_homescreen, "stockfish")


# ============= CHESS BOT-SPECIFIC FUNCTIONS =============

def initialize_chess_bot():
    """Initialize the chess bot"""
    global chess_bot_instance

    try:
        from chess_bot import ChessBot
        chess_bot_instance = ChessBot()
        return True
    except ImportError as e:
        print(f"Error importing chess_bot: {e}")
        return False


def chess_bot_make_move():
    """Make chess bot move using the ChessBot class"""
    global game_board, game_state, chess_bot_instance

    if not game_state["game_active"] or game_state["my_turn"]:
        return

    try:
        # Update the status to show the bot is thinking
        if status_label and status_label.winfo_exists():
            game_canvas.after(0, lambda: status_label.config(text="Bot thinking..."))

        # Use the ChessBot class
        best_move = chess_bot_instance.get_best_move(game_board, max_depth=difficulty)

        if best_move and best_move in game_board.legal_moves:
            game_board.push(best_move)
            game_state["selected"] = None
            game_state["current_player"] = chess.WHITE
            game_state["my_turn"] = True

            if game_canvas and game_canvas.winfo_exists():
                game_canvas.after(0, update_board)

            if status_label and status_label.winfo_exists():
                game_canvas.after(0, lambda: status_label.config(text="Your turn"))

            if game_board.is_game_over():
                result_text = get_game_result()
                game_state["game_active"] = False

                return_to_homescreen = getattr(game_canvas.master, 'return_to_homescreen', None)
                if return_to_homescreen:
                    game_canvas.after(1000, lambda: show_game_over(result_text, return_to_homescreen))
        else:
            print("Chess bot returned no valid move")
            # Fallback to a random move if the bot fails
            legal_moves = list(game_board.legal_moves)
            if legal_moves:
                import random
                fallback_move = random.choice(legal_moves)
                game_board.push(fallback_move)
                game_state["selected"] = None
                game_state["current_player"] = chess.WHITE
                game_state["my_turn"] = True

                if game_canvas and game_canvas.winfo_exists():
                    game_canvas.after(0, update_board)

    except Exception as e:
        print(f"Chess bot move error: {e}")
        # Try to continue the game even if the bot fails
        if game_canvas and game_canvas.winfo_exists():
            game_canvas.after(0, lambda: status_label.config(text="Bot error - Your turn"))


def show_chess_bot_difficulty_selection(window, return_to_homescreen):
    """Show difficulty selection dialog for Chess Bot"""
    global difficulty, chess_bot_instance

    overlay = tk.Frame(window, bg="black")
    overlay.place(x=0, y=0, relwidth=1, relheight=1)

    # Main frame
    main_frame = tk.Frame(overlay, bg="#222222", relief="ridge", bd=3)
    main_frame.place(relx=0.5, rely=0.5, anchor="center", width=450, height=500)

    tk.Label(main_frame, text="Select Bot Difficulty", font=("Arial", 20, "bold"),
             bg="#222222", fg="white").pack(pady=20)

    difficulties = [
        ("Beginner", 2, "Very easy - Good for learning"),
        ("Easy", 3, "Easy - Makes some mistakes"),
        ("Medium", 4, "Medium - Decent opponent"),
        ("Hard", 5, "Hard - Strong tactical play")
    ]

    selected = tk.IntVar(value=2)

    for name, level, description in difficulties:
        frame = tk.Frame(main_frame, bg="#222222")
        frame.pack(pady=5, padx=20, fill="x")

        tk.Radiobutton(frame, text=f"{name} (Depth {level})",
                       variable=selected, value=level, font=("Arial", 12, "bold"),
                       bg="#222222", fg="white", selectcolor="#444444").pack(anchor="w")

        tk.Label(frame, text=description, font=("Arial", 10),
                 bg="#222222", fg="#CCCCCC").pack(anchor="w", padx=20)

    def start_game():
        global difficulty, chess_bot_instance
        difficulty = selected.get()

        # Initialize the chess bot first
        if not initialize_chess_bot():
            tkinter.messagebox.showerror("Error", "Failed to initialize Chess Bot!\nMake sure chess_bot.py exists.")
            return

        # Configure the bot's time limit based on difficulty
        time_limits = {2: 1.0, 3: 2.0, 4: 3.0, 5: 5.0}
        if hasattr(chess_bot_instance, 'time_limit'):
            chess_bot_instance.time_limit = time_limits.get(difficulty, 5.0)

        overlay.destroy()
        start_chess_bot_game(window, return_to_homescreen)

    tk.Button(main_frame, text="Start Game", command=start_game,
              font=("Arial", 12), bg="green", fg="white", width=15).pack(pady=15)
    tk.Button(main_frame, text="Cancel", command=overlay.destroy,
              font=("Arial", 12), bg="red", fg="white", width=15).pack(pady=5)


def start_chess_bot_game(window, return_to_homescreen):
    """Start the chess bot game"""
    global game_board, game_state, chess_bot_instance

    # Only initialize if not already done
    if chess_bot_instance is None:
        if not initialize_chess_bot():
            tkinter.messagebox.showerror("Error", "Failed to initialize Chess Bot!\nMake sure chess_bot.py exists.")
            return

    # Reset game and clear transposition table
    game_board = chess.Board()
    game_state = {
        "selected": None, "current_player": chess.WHITE,
        "my_color": chess.WHITE, "my_turn": True, "game_active": True
    }

    # Clear the bot's transposition table for a fresh start
    if hasattr(chess_bot_instance, 'tt'):
        chess_bot_instance.tt = chess_bot_instance.tt.__class__()

    create_game_interface(window, return_to_homescreen, "chess_bot")


# ============= MAIN ENTRY POINTS =============

def play_with_stockfish(window, return_to_homescreen, player_name_param="Player1"):
    """Main entry point for Stockfish games"""
    global player_name
    player_name = player_name_param
    show_stockfish_difficulty_selection(window, return_to_homescreen)


def play_with_chess_bot(window, return_to_homescreen, player_name_param="Player1"):
    """Main entry point for Chess Bot games"""
    global player_name
    player_name = player_name_param
    show_chess_bot_difficulty_selection(window, return_to_homescreen)