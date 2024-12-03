import chess
import pygame
from pygame.time import delay

import chess_bot

BOARD_HEIGHT = 600
BOARD_WIDTH = 600
timer = pygame.time.Clock()
fps = 30

piece_images = {}


def load_images():
    timer.tick(fps)
    white_rook = pygame.image.load('assets\\pieces\\white rook.png')
    white_rook = pygame.transform.scale(white_rook, (60, 60))
    piece_images['r'] = white_rook
    white_knight = pygame.image.load('assets\\pieces\\white knight.png')
    white_knight = pygame.transform.scale(white_knight, (60, 60))
    piece_images['n'] = white_knight
    white_bishop = pygame.image.load('assets\\pieces\\white bishop.png')
    white_bishop = pygame.transform.scale(white_bishop, (60, 60))
    piece_images['b'] = white_bishop
    white_king = pygame.image.load('assets\\pieces\\white king.png')
    white_king = pygame.transform.scale(white_king, (60, 60))
    piece_images['k'] = white_king
    white_queen = pygame.image.load('assets\\pieces\\white queen.png')
    white_queen = pygame.transform.scale(white_queen, (60, 60))
    piece_images['q'] = white_queen
    white_pawn = pygame.image.load('assets\\pieces\\white pawn.png')
    white_pawn = pygame.transform.scale(white_pawn, (60, 60))
    piece_images['p'] = white_pawn

    black_rook = pygame.image.load('assets\\pieces\\black rook.png')
    black_rook = pygame.transform.scale(black_rook, (60, 60))
    piece_images['R'] = black_rook
    black_knight = pygame.image.load('assets\\pieces\\black knight.png')
    black_knight = pygame.transform.scale(black_knight, (60, 60))
    piece_images['N'] = black_knight
    black_bishop = pygame.image.load('assets\\pieces\\black bishop.png')
    black_bishop = pygame.transform.scale(black_bishop, (60, 60))
    piece_images['B'] = black_bishop
    black_king = pygame.image.load('assets\\pieces\\black king.png')
    black_king = pygame.transform.scale(black_king, (60, 60))
    piece_images['K'] = black_king
    black_queen = pygame.image.load('assets\\pieces\\black queen.png')
    black_queen = pygame.transform.scale(black_queen, (60, 60))
    piece_images['Q'] = black_queen
    black_pawn = pygame.image.load('assets\\pieces\\black pawn.png')
    black_pawn = pygame.transform.scale(black_pawn, (60, 60))
    piece_images['P'] = black_pawn


def position2pixel(position):
    row, col = position
    return row * (BOARD_WIDTH // 8) + 5, col * (BOARD_HEIGHT // 8) + 5


def pixel2position(pixel):
    x, y = pixel
    return x * 8 // BOARD_WIDTH, y * 8 // BOARD_HEIGHT


def position2square_name(position):
    row, col = position
    square_value = row + col * 8
    return chr(square_value % 8 + ord('a')) + str(8 - square_value // 8)


def square_name2position(square_name):
    return ord(square_name[0]) - 97, 8 - int(square_name[1])


def draw_board(screen):
    for col in range(8):
        for row in range(8):
            if col % 2 ^ row % 2:
                color = (131, 203, 114)
            else:
                color = (220, 226, 214)
            pygame.draw.rect(screen, color,
                             [col * (BOARD_WIDTH // 8), row * (BOARD_HEIGHT // 8), BOARD_WIDTH // 8, BOARD_HEIGHT // 8])


def from_fen_draw_pieces(screen, fen):
    fen = fen.split()[0].replace('/', '')
    i = 0
    for piece_fen_representation in fen:
        if piece_fen_representation.isdigit():
            i += int(piece_fen_representation)
        else:
            screen.blit(piece_images[piece_fen_representation], position2pixel((i % 8, i // 8)))
            i += 1


def draw_on_square(screen, position):
    col, row = position
    pygame.draw.rect(screen, (105, 105, 105),
                     [col * (BOARD_WIDTH // 8), row * (BOARD_HEIGHT // 8), BOARD_WIDTH // 8, BOARD_HEIGHT // 8], 3)
    # screen.blit(screen, (0, 0))

def main():
    pygame.init()
    screen = pygame.display.set_mode((BOARD_WIDTH, BOARD_HEIGHT))

    load_images()

    UCI_move = ''

    board = chess.Board()

    draw_board(screen)
    from_fen_draw_pieces(screen, board.fen())
    selection = 0
    position = None
    is_running = True
    current_player = chess.WHITE

    while is_running:
        timer.tick(fps)

        draw_board(screen)
        from_fen_draw_pieces(screen, board.fen())

        if selection == 1:
            draw_on_square(screen, position)

            for move in board.legal_moves:
                if move.from_square == chess.parse_square(position2square_name(position)):
                    x, y = position2pixel(square_name2position(chess.square_name(move.to_square)))
                    pygame.draw.circle(screen, (105, 105, 105), (x + (600 // 16) - 5, y + (600 // 16) - 5), 5)

        screen.blit(screen, (0, 0))
        pygame.display.flip()



        if current_player == chess.BLACK:
            board.push(chess_bot.minimax(board, 4, chess.WHITE, chess.WHITE)[0])
            current_player = not current_player


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

            elif current_player == chess.WHITE and event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT: #
                position = pixel2position(pygame.mouse.get_pos())
                piece = board.piece_at(chess.parse_square(position2square_name(position)))
                if piece is not None and piece.color == current_player:
                    selection = 1
                    UCI_move = position2square_name(position)
                else:
                    selection = 0

                wanted_move = position2square_name(position)
                if UCI_move != '' and UCI_move != wanted_move:

                    UCI_move += wanted_move
                    move = chess.Move.from_uci(UCI_move)
                    if board.is_legal(move):
                        board.push(move)
                        current_player = not current_player
                    UCI_move = ''

        if board.is_checkmate() or board.is_stalemate() or board.is_repetition(3):
            print('game ended')
            is_running = False

    draw_board(screen)
    from_fen_draw_pieces(screen, board.fen())
    pygame.display.flip()
    delay(500)
    pygame.quit()


if __name__ == '__main__':
    main()