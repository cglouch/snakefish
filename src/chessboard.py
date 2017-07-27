import numpy as np

from constants import Color

class ChessBoard(object):
    def __init__(self):
        self.pieces = np.zeros((2,6), dtype=np.uint64) # 2 sides, 6 piece bitboards per side
        self.combined_side = np.zeros(2, dtype=np.uint64) # Combined bitboard for all pieces of given side
        self.combined_all = np.uint64(0) # Combined bitboard for all pieces on the board
        self.to_move = Color.WHITE
