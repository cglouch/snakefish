from enum import Enum
import numpy as np

from chessboard import ChessBoard
from constants import Piece
import tables
import bitboard
import movegen

class Score(Enum):
    PAWN = np.int32(100)
    KNIGHT = np.int32(300)
    BISHOP = np.int32(300)
    ROOK = np.int32(500)
    QUEEN = np.int32(900)
    CHECKMATE = np.int32(-1000000)
    CENTER = np.int32(5)
    MOVE = np.int32(5)

def evaluate(board):
    return eval_pieces(board) + eval_center(board) + eval_moves(board)

def eval_pieces(board):
    return (Score.PAWN.value * bitboard.pop_count(board.get_piece_bb(Piece.PAWN))
        + Score.KNIGHT.value * bitboard.pop_count(board.get_piece_bb(Piece.KNIGHT)) 
        + Score.BISHOP.value * bitboard.pop_count(board.get_piece_bb(Piece.BISHOP))
        + Score.ROOK.value * bitboard.pop_count(board.get_piece_bb(Piece.ROOK))
        + Score.QUEEN.value * bitboard.pop_count(board.get_piece_bb(Piece.QUEEN)))

def eval_center(board):
    return Score.CENTER.value * bitboard.pop_count(board.combined_color[board.color] & tables.center)

def eval_moves(board):
    num = len(list(movegen.gen_legal_moves(board)))
    if num == 0:
        return Score.CHECKMATE.value
    else:
        return Score.MOVE.value * np.int32(num)
