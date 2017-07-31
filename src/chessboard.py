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

    #TODO: make function for updating piece bitboards so i dont forget to updated combined_color/combined_all

    def  __str__(self):
        board_str = []
        for r in reversed(Rank):
            for f in File:
                sq = Square.from_position(r, f)
                white_piece = self.piece_on(sq, Color.WHITE)
                black_piece = self.piece_on(sq, Color.BLACK)
                if white_piece is not None:
                    board_str.append(white_piece.to_char().upper())
                elif black_piece is not None:
                    board_str.append(black_piece.to_char())
                else:
                    board_str.append('.')
            board_str.append('\n')
        board_str = ''.join(board_str)
        info_str = "%s to move" % self.color.name
        return "%s%s" % (board_str, info_str)

    def get_piece_bb(self, piece, color=None):
        # NOTE: Defaults to current color
        if color is None:
            color = self.color
        return self.pieces[color][piece]

    def piece_on(self, sq, color=None):
        # NOTE: Defaults to current color
        if color is None:
            color = self.color
        return next(
            (p for p in Piece if 
                bitboard.is_set(self.get_piece_bb(p, color), sq)),
            None)

    def apply_move(self, move):
        pass

    def init_game(self):
        self.pieces[Color.WHITE][Piece.PAWN] = np.uint64(0x000000000000FF00)
        self.pieces[Color.WHITE][Piece.KNIGHT] = np.uint64(0x0000000000000042)
        self.pieces[Color.WHITE][Piece.BISHOP] = np.uint64(0x0000000000000024)
        self.pieces[Color.WHITE][Piece.ROOK] = np.uint64(0x0000000000000081)
        self.pieces[Color.WHITE][Piece.QUEEN] = np.uint64(0x0000000000000008)
        self.pieces[Color.WHITE][Piece.KING] = np.uint64(0x0000000000000010)

        self.pieces[Color.BLACK][Piece.PAWN] = np.uint64(0x00FF000000000000)
        self.pieces[Color.BLACK][Piece.KNIGHT] = np.uint64(0x4200000000000000)
        self.pieces[Color.BLACK][Piece.BISHOP] = np.uint64(0x2400000000000000)
        self.pieces[Color.BLACK][Piece.ROOK] = np.uint64(0x8100000000000000)
        self.pieces[Color.BLACK][Piece.QUEEN] = np.uint64(0x0800000000000000)
        self.pieces[Color.BLACK][Piece.KING] = np.uint64(0x1000000000000000)

        for p in Piece:
            for c in Color:
                self.combined_color[c] |= self.pieces[c][p]

        self.combined_all = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]
