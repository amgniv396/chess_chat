import tkinter as tk
import chess

BOARD_SIZE = 800

def start_game(window, return_to_home):
    # Clear window
    for widget in window.winfo_children():
        widget.destroy()

    # Game screen frame
    game_frame = tk.Frame(window, bg="white")
    game_frame.pack(fill="both", expand=True)

    # Chess canvas
    chess_canvas = tk.Canvas(game_frame, width=BOARD_SIZE, height=BOARD_SIZE, bg="white", bd=5, relief="ridge")
    chess_canvas.pack(pady=20)

    # Buttons frame
    buttons_frame = tk.Frame(game_frame, bg="white")
    buttons_frame.pack()

    draw_button = tk.Button(buttons_frame, text="Offer Draw", width=15)
    draw_button.pack(side="left", padx=10)

    resign_button = tk.Button(buttons_frame, text="Resign", width=15,
                               command=lambda: return_to_home(window))
    resign_button.pack(side="left", padx=10)

    # Set up chess logic
    setup_chess(chess_canvas)

def setup_chess(chess_canvas):
    board = chess.Board()

    SQUARE_SIZE = BOARD_SIZE // 8

    def draw_board():
        colors = ["#83CB72", "#DCE2D6"]
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                chess_canvas.create_rectangle(
                    col * SQUARE_SIZE, row * SQUARE_SIZE,
                    (col + 1) * SQUARE_SIZE, (row + 1) * SQUARE_SIZE,
                    fill=color, outline=""
                )

    draw_board()

    # You can extend this to draw pieces, handle clicks, etc.
