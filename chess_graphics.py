from idlelib.pyparse import trans
from tkinter import Canvas

import ttkbootstrap as ttk
import tkinter as tk
from PIL import Image, ImageTk
import chess

# Board and Piece Dimensions
BOARD_SIZE = 800
SQUARE_SIZE = BOARD_SIZE // 8

PIECE_SIZE_TO_SQUARE = 15

piece_images = {}
COLORS = {'odd': '#83CB72', 'even': '#DCE2D6'}

CIRCLE_CONST = 35


def load_images():
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
    for row in range(8):
        for col in range(8):
            color = COLORS['odd'] if (row + col) % 2 == 0 else COLORS['even']
            canvas.create_rectangle(col * SQUARE_SIZE, row * SQUARE_SIZE, (col + 1) * SQUARE_SIZE,
                                    (row + 1) * SQUARE_SIZE, fill=color, outline="")


def draw_pieces(canvas, fen: str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
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


def on_square_click(event, canvas, board, game_state):
    row = event.y // SQUARE_SIZE
    col = event.x // SQUARE_SIZE
    square = chess.square(col, 7 - row)
    piece = board.piece_at(square)

    if game_state["selected"]:
        move = chess.Move(game_state["selected"], square)
        if move in board.legal_moves:
            board.push(move)
            game_state["selected"] = None
            game_state["current_player"] = not game_state["current_player"]
        else:
            game_state["selected"] = square
    elif piece and piece.color == game_state["current_player"]:
        game_state["selected"] = square

    update_board(canvas, board, game_state)


# Update the board and pieces
def update_board(canvas, board, game_state):
    canvas.delete("all")
    draw_board(canvas)
    draw_pieces(canvas, board.fen())

    # Highlight selected square
    if game_state["selected"]:
        row = 7 - chess.square_rank(game_state["selected"])
        col = chess.square_file(game_state["selected"])
        x1 = col * SQUARE_SIZE
        y1 = row * SQUARE_SIZE
        x2 = x1 + SQUARE_SIZE
        y2 = y1 + SQUARE_SIZE
        canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3)

        for move in board.legal_moves:
            if move.from_square == game_state["selected"]:
                row = 7 - move.to_square // 8
                col = move.to_square % 8
                x1 = col * SQUARE_SIZE
                y1 = row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                canvas.create_oval(x1 + CIRCLE_CONST, y1 + CIRCLE_CONST, x2 - CIRCLE_CONST, y2 - CIRCLE_CONST,
                                   fill="gray")


# Main function
def main():
    app = ttk.Window(themename="darkly")
    app.title("chess-chat game")
    app.geometry(f"{BOARD_SIZE}x{BOARD_SIZE}")

    load_images()

    board = chess.Board()
    game_state = {"selected": None, "current_player": chess.WHITE}

    canvas = ttk.tk.Canvas(app, width=BOARD_SIZE, height=BOARD_SIZE)
    canvas.pack()

    draw_board(canvas)
    draw_pieces(canvas)

    canvas.bind("<Button-1>", lambda event: on_square_click(event, canvas, board, game_state))

    app.mainloop()


if __name__ == "__main__":
    main()