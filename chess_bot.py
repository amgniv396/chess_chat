import chess
import random
import time
import hashlib

# Improved piece values based on modern chess theory
PIECE_VALUES = {
    'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000
}

# Piece-square tables for positional evaluation
PAWN_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0
]

KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]

ROOK_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0
]

QUEEN_TABLE = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]

KING_TABLE_MIDDLEGAME = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20
]

KING_TABLE_ENDGAME = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

PIECE_SQUARE_TABLES = {
    'p': PAWN_TABLE,
    'n': KNIGHT_TABLE,
    'b': BISHOP_TABLE,
    'r': ROOK_TABLE,
    'q': QUEEN_TABLE,
    'k': KING_TABLE_MIDDLEGAME
}


class TranspositionTable:
    def __init__(self, size=1000000):
        self.table = {}
        self.size = size

    def store(self, key, depth, value, flag, best_move=None):
        if len(self.table) >= self.size:
            # Simple replacement strategy
            self.table.clear()

        self.table[key] = {
            'depth': depth,
            'value': value,
            'flag': flag,  # 'exact', 'lower', 'upper'
            'best_move': best_move
        }

    def lookup(self, key):
        return self.table.get(key)


class ChessBot:
    def __init__(self):
        self.tt = TranspositionTable()
        self.nodes_searched = 0
        self.time_limit = 5.0  # seconds
        self.start_time = 0

    def get_piece_square_value(self, piece, square, is_endgame=False):
        """Get positional value for a piece on a given square"""
        piece_type = piece.symbol().lower()

        if piece_type == 'k' and is_endgame:
            table = KING_TABLE_ENDGAME
        else:
            table = PIECE_SQUARE_TABLES.get(piece_type, [0] * 64)

        # Flip square for black pieces
        if piece.color == chess.BLACK:
            square = chess.square_mirror(square)

        return table[square]

    def is_endgame(self, board):
        """Determine if we're in endgame based on material"""
        queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
        minors = (len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.WHITE)) +
                  len(board.pieces(chess.BISHOP, chess.BLACK)) + len(board.pieces(chess.KNIGHT, chess.BLACK)))

        # Endgame if no queens or very few minor pieces
        return queens == 0 or (queens == 2 and minors <= 1)

    def evaluate_position(self, board):
        """Comprehensive position evaluation"""
        if board.is_checkmate():
            return -20000 if board.turn else 20000

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        is_endgame = self.is_endgame(board)

        # Material and positional evaluation
        for square, piece in board.piece_map().items():
            piece_value = PIECE_VALUES[piece.symbol().lower()]
            positional_value = self.get_piece_square_value(piece, square, is_endgame)

            total_value = piece_value + positional_value

            if piece.color == chess.WHITE:
                score += total_value
            else:
                score -= total_value

        # Mobility evaluation
        white_mobility = len(list(board.legal_moves)) if board.turn == chess.WHITE else 0
        board.turn = not board.turn
        black_mobility = len(list(board.legal_moves)) if board.turn == chess.BLACK else 0
        board.turn = not board.turn

        score += (white_mobility - black_mobility) * 10

        # King safety in middlegame
        if not is_endgame:
            white_king_square = board.king(chess.WHITE)
            black_king_square = board.king(chess.BLACK)

            # Penalize exposed kings
            white_king_attackers = len(board.attackers(chess.BLACK, white_king_square))
            black_king_attackers = len(board.attackers(chess.WHITE, black_king_square))

            score -= white_king_attackers * 50
            score += black_king_attackers * 50

        # Pawn structure evaluation
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)

        # Doubled pawns penalty
        for file in chess.FILE_NAMES:
            file_index = ord(file) - ord('a')
            white_pawns_in_file = len([s for s in white_pawns if chess.square_file(s) == file_index])
            black_pawns_in_file = len([s for s in black_pawns if chess.square_file(s) == file_index])

            if white_pawns_in_file > 1:
                score -= 20 * (white_pawns_in_file - 1)
            if black_pawns_in_file > 1:
                score += 20 * (black_pawns_in_file - 1)

        return score if board.turn == chess.WHITE else -score

    def order_moves(self, board, moves, tt_best_move=None):
        """Order moves for better alpha-beta pruning"""
        move_scores = []

        for move in moves:
            score = 0

            # Prioritize transposition table best move
            if tt_best_move and move == tt_best_move:
                score += 10000

            # Captures
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    moving_piece = board.piece_at(move.from_square)
                    # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
                    score += PIECE_VALUES[captured_piece.symbol().lower()] - PIECE_VALUES[
                        moving_piece.symbol().lower()] + 1000

            # Checks
            board.push(move)
            if board.is_check():
                score += 500
            board.pop()

            # Promotions
            if move.promotion:
                score += PIECE_VALUES[chess.piece_name(move.promotion)]

            # Castling
            if board.is_castling(move):
                score += 200

            move_scores.append((move, score))

        # Sort by score (descending)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def get_board_hash(self, board):
        """Generate a hash for the board position"""
        # Use FEN string as a simple hash (you could use a more sophisticated method)
        fen = board.fen()
        return hashlib.md5(fen.encode()).hexdigest()

    def minimax(self, board, depth, alpha, beta, maximizing_player, start_time):
        """Enhanced minimax with alpha-beta pruning and transposition table"""
        self.nodes_searched += 1

        # Time management
        if time.time() - start_time > self.time_limit:
            return None, self.evaluate_position(board)

        # Transposition table lookup
        board_hash = self.get_board_hash(board)
        tt_entry = self.tt.lookup(board_hash)
        tt_best_move = None

        if tt_entry and tt_entry['depth'] >= depth:
            if tt_entry['flag'] == 'exact':
                return tt_entry['best_move'], tt_entry['value']
            elif tt_entry['flag'] == 'lower' and tt_entry['value'] >= beta:
                return tt_entry['best_move'], tt_entry['value']
            elif tt_entry['flag'] == 'upper' and tt_entry['value'] <= alpha:
                return tt_entry['best_move'], tt_entry['value']
            tt_best_move = tt_entry['best_move']

        # Terminal conditions
        if depth == 0 or board.is_game_over():
            value = self.evaluate_position(board)
            self.tt.store(board_hash, depth, value, 'exact')
            return None, value

        moves = list(board.legal_moves)
        if not moves:
            return None, self.evaluate_position(board)

        # Move ordering
        moves = self.order_moves(board, moves, tt_best_move)

        best_move = moves[0]
        original_alpha = alpha

        if maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                board.push(move)
                _, eval_score = self.minimax(board, depth - 1, alpha, beta, False, start_time)
                board.pop()

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move

                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff

            # Store in transposition table
            if max_eval <= original_alpha:
                flag = 'upper'
            elif max_eval >= beta:
                flag = 'lower'
            else:
                flag = 'exact'

            self.tt.store(board_hash, depth, max_eval, flag, best_move)
            return best_move, max_eval

        else:
            min_eval = float('inf')
            for move in moves:
                board.push(move)
                _, eval_score = self.minimax(board, depth - 1, alpha, beta, True, start_time)
                board.pop()

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move

                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff

            # Store in transposition table
            if min_eval <= original_alpha:
                flag = 'upper'
            elif min_eval >= beta:
                flag = 'lower'
            else:
                flag = 'exact'

            self.tt.store(board_hash, depth, min_eval, flag, best_move)
            return best_move, min_eval

    def iterative_deepening(self, board, max_depth=6):
        """Iterative deepening search with time management"""
        self.start_time = time.time()
        self.nodes_searched = 0

        best_move = None
        best_eval = 0

        for depth in range(1, max_depth + 1):
            if time.time() - self.start_time > self.time_limit:
                break

            try:
                move, eval_score = self.minimax(
                    board, depth, float('-inf'), float('inf'),
                    board.turn == chess.WHITE, self.start_time
                )

                if move:
                    best_move = move
                    best_eval = eval_score

                elapsed_time = time.time() - self.start_time
                print(f"Depth {depth}: {move} (eval: {eval_score:.2f}, "
                      f"nodes: {self.nodes_searched}, time: {elapsed_time:.2f}s)")

            except KeyboardInterrupt:
                break

        return best_move, best_eval

    def get_best_move(self, board, max_depth=6):
        """Get the best move using iterative deepening"""
        if not list(board.legal_moves):
            return None

        move, eval_score = self.iterative_deepening(board, max_depth)

        print(f"Final choice: {move} (eval: {eval_score:.2f})")
        return move


# Example usage:
if __name__ == "__main__":
    bot = ChessBot()
    board = chess.Board()

    # Example: Get best move for starting position
    best_move = bot.get_best_move(board, max_depth=5)
    print(f"Best move: {best_move}")