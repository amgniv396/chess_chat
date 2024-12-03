import chess
import random

pieces_value = {'k': 999,
                'q': 9,
                'r': 5,
                'b': 3,
                'n': 3,
                'p': 1
                }

def minimax(board, depth, maximizing_player, maximizing_color, alpha = float("-inf"), beta = float("inf")):
    if depth == 0 or board.is_checkmate() or board.is_stalemate() or board.is_repetition():
        return None, evaluate(board, maximizing_color, maximizing_player, depth)

    moves = list(board.legal_moves)
    best_move = moves[0]

    if maximizing_player:
        max_eval = float("-inf")
        for move in moves:
            board.push(move)
            _, current_eval = minimax(board, depth - 1, False, maximizing_color, alpha, beta)
            board.pop()
            if current_eval > max_eval:
                max_eval = current_eval
                best_move = move
            elif current_eval == max_eval and random.randint(0,1):
                max_eval = current_eval
                best_move = move

            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return best_move, max_eval
    else:
        min_eval = float("inf")
        for move in moves:
            board.push(move)
            _, current_eval = minimax(board, depth - 1, True, maximizing_color, alpha, beta)
            board.pop()
            if current_eval < min_eval:
                min_eval = current_eval
                best_move = move
            elif current_eval == min_eval and random.randint(0,1):
                min_eval = current_eval
                best_move = move

            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return best_move, min_eval

def evaluate(board, maximizing_color, maximizing_player, depth):
    white_count, black_count = 0, 0
    for piece in board.piece_map().values():
        if str(piece).islower():
            white_count += pieces_value[str(piece)]
        else:
            black_count += pieces_value[str(piece).lower()]

    if board.is_checkmate():
        if maximizing_player != maximizing_color:
            return 9999 + depth
        else:
            return -9999 - depth
    if board.is_stalemate() or board.is_repetition():
        return 0

    if maximizing_color == chess.WHITE:
        return white_count - black_count + depth
    else:
        return black_count - white_count + depth