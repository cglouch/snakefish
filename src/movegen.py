import numpy as np

import tables
import bitboard
from constants import Rank, File, Color, Piece
from move import Move


# Some helper functions for sliding pieces

def get_diag_moves_bb(i, occ):
    """
    i is index of square
    occ is the combined occupancy of the board
    """
    f = i & np.uint8(7)
    occ = tables.DIAG_MASKS[i] & occ # isolate diagonal occupancy
    occ = (tables.FILES[File.A] * occ) >> np.uint8(56) # map to first rank
    occ = tables.FILES[File.A] * tables.FIRST_RANK_MOVES[f][occ] # lookup and map back to diagonal
    return tables.DIAG_MASKS[i] & occ


def get_antidiag_moves_bb(i, occ):
    """
    i is index of square
    occ is the combined occupancy of the board
    """
    f = i & np.uint8(7)
    occ = tables.ANTIDIAG_MASKS[i] & occ # isolate antidiagonal occupancy
    occ = (tables.FILES[File.A] * occ) >> np.uint8(56) # map to first rank
    occ = tables.FILES[File.A] * tables.FIRST_RANK_MOVES[f][occ] # lookup and map back to antidiagonal
    return tables.ANTIDIAG_MASKS[i] & occ


def get_rank_moves_bb(i, occ):
    """
    i is index of square
    occ is the combined occupancy of the board
    """
    f = i & np.uint8(7)
    occ = tables.RANK_MASKS[i] & occ # isolate rank occupancy
    occ = (tables.FILES[File.A] * occ) >> np.uint8(56) # map to first rank
    occ = tables.FILES[File.A] * tables.FIRST_RANK_MOVES[f][occ] # lookup and map back to rank
    return tables.RANK_MASKS[i] & occ


def get_file_moves_bb(i, occ):
    """
    i is index of square
    occ is the combined occupancy of the board
    """
    f = i & np.uint8(7)
    occ = tables.FILES[File.A] & (occ >> f)
    occ = (tables.A1H8_DIAG * occ) >> np.uint8(56)
    occ = tables.A1H8_DIAG * tables.FIRST_RANK_MOVES[(i^np.uint8(56)) >> 3][occ]
    return (tables.FILES[File.H] & occ) >> (f ^ np.uint8(7))


# Moveset functions for each piece

def get_king_moves_bb(sq, board):
    return tables.KING_MOVES[sq.index] & ~board.combined_color[board.color]

def get_knight_moves_bb(sq, board):
    return tables.KNIGHT_MOVES_BB[sq.index] & ~board.combined_color[board.color]

def get_pawn_moves_bb(sq, board):
    attacks = tables.PAWN_ATTACKS[board.color][sq.index] & board.combined_color[~board.color]
    quiets = tables.EMPTY_BB
    white_free = Square(sq.index + np.uint8(8)).to_bitboard() & board.combined_all == tables.EMPTY_BB 
    black_free = Square(sq.index - np.uint8(8)).to_bitboard() & board.combined_all == tables.EMPTY_BB 
    if (board.color == color.WHITE and white_free) or (board.color == color.BLACK and black_free):
        quiets = tables.PAWN_QUIETS[board.color][sq.index] & ~board.combined_all
    return attacks | quiets

def get_bishop_moves_bb(sq, board):
    return (get_diag_moves_bb(sq.index, board.combined_all) 
        ^ get_antidiag_moves_bb(sq.index, board.combined_all))
        & ~board.combined_color

def get_rook_moves_bb(sq, board):
    return (get_rank_moves_bb(sq.index, board.combined_all)
        ^ get_file_moves_bb(sq.index, board.combined_all))
        & ~board.combined_color

def get_queen_moves_bb(sq, board):
    return get_rook_moves_bb(sq, board) | get_bishop_moves_bb(sq, board)

moveset_functions = [0] * 6
moveset_functions[Piece.PAWN] = get_pawn_moves_bb
moveset_functions[Piece.KNIGHT] = get_knight_moves_bb
moveset_functions[Piece.BISHOP] = get_bishop_moves_bb
moveset_functions[Piece.ROOK] = get_rook_moves_bb
moveset_functions[Piece.QUEEN] = get_queen_moves_bb
moveset_functions[Piece.KING] = get_king_moves_bb


# Move generators

def gen_moves(board):
    for piece in Piece:
        piece_bb = board.pieces[board.color][piece]
        moveset_function = moveset_functions[piece]

        for src in bitboard.occupied_squares(piece_bb):
            moveset = moveset_function(src, board)
            for dest in bitboard.occupied_squares(moveset):
                yield Move(src, dest)


