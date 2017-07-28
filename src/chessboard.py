import numpy as np

import bitboard
from constants import Color, File, Rank, Piece
from square import Square

class ChessBoard(object):
    def __init__(self):
        self.pieces = np.zeros((2,6), dtype=np.uint64) # 2 sides, 6 piece bitboards per side
        self.combined_color = np.zeros(2, dtype=np.uint64) # Combined bitboard for all pieces of given side
        self.combined_all = np.uint64(0) # Combined bitboard for all pieces on the board
        self.color = Color.WHITE # Color to move

    def  __str__(self):
        board_str = []
        for r in reversed(Rank):
            for f in File:
                sq = Square.from_position(r, f)
                white_piece = self.get_piece(sq, Color.WHITE)
                black_piece = self.get_piece(sq, Color.BLACK)
                if white_piece:
                    board_str.append(white_piece.to_char().upper())
                elif black_piece:
                    board_str.append(black_piece.to_char())
                else:
                    board_str.append('.')
            board_str.append('\n')
        board_str = ''.join(board_str)
        info_str = "%s to move" % self.color.name
        return "%s%s" % (board_str, info_str)

    def get_piece_bb(self, piece, color=self.color):
        # NOTE: Defaults to current color
        return self.pieces[color][piece]

    def get_piece(self, sq, color=self.color):
        # NOTE: Defaults to current color
        return next(
            (p for p in Piece if 
                bitboard.is_set(self.get_piece_bb(p, color), sq)),
            None)

    def apply_move(self, move):
        pass

    def is_legal(self, move):
        pass
