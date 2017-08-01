import numpy as np

from chessboard import ChessBoard
import movegen

def perft(board, depth):
    if depth == 0:
        return 1
    count = 0
    moves = movegen.gen_legal_moves(board)
    for m in moves:
        count += perft(board.apply_move(m), depth-1)
    return count

def test_new():
    b = ChessBoard()
    b.init_game()
    assert perft(b, 0) == 1
    assert perft(b, 1) == 20
    assert perft(b, 2) == 400
    assert perft(b, 3) == 8902
    assert perft(b, 4) == 197281


