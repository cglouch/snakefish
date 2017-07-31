import itertools
import numpy as np

import tables
import bitboard
from constants import Rank, File, Color, Piece
from move import Move
from square import Square
from chessboard import ChessBoard


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
    f = i % np.uint8(7)
    # Shift to A file
    occ = tables.FILES[File.A] & (occ >> f)
    # Map occupancy and index to first rank
    occ = (tables.A1H8_DIAG * occ) >> np.uint8(56)
    first_rank_index = (i ^ np.uint8(56)) >> np.uint8(3)
    # Lookup moveset and map back to H file
    occ = tables.A1H8_DIAG * tables.FIRST_RANK_MOVES[first_rank_index][occ]
    # Isolate H file and shift back to original file
    return (tables.FILES[File.H] & occ) >> (f ^ np.uint8(7))


# Moveset functions for each piece

def get_king_moves_bb(sq, board):
    return tables.KING_MOVES[sq.index] & ~board.combined_color[board.color]

def get_knight_moves_bb(sq, board):
    return tables.KNIGHT_MOVES[sq.index] & ~board.combined_color[board.color]

def get_pawn_moves_bb(sq, board):
    attacks = tables.PAWN_ATTACKS[board.color][sq.index] & board.combined_color[~board.color]
    quiets = tables.EMPTY_BB
    white_free = Square(sq.index + np.uint8(8)).to_bitboard() & board.combined_all == tables.EMPTY_BB 
    black_free = Square(sq.index - np.uint8(8)).to_bitboard() & board.combined_all == tables.EMPTY_BB 
    if (board.color == Color.WHITE and white_free) or (board.color == Color.BLACK and black_free):
        quiets = tables.PAWN_QUIETS[board.color][sq.index] & ~board.combined_all
    return attacks | quiets

def get_bishop_moves_bb(sq, board):
    return ((get_diag_moves_bb(sq.index, board.combined_all) 
        ^ get_antidiag_moves_bb(sq.index, board.combined_all))
        & ~board.combined_color[board.color])

def get_rook_moves_bb(sq, board):
    return ((get_rank_moves_bb(sq.index, board.combined_all)
        ^ get_file_moves_bb(sq.index, board.combined_all))
        & ~board.combined_color[board.color])

def get_queen_moves_bb(sq, board):
    return get_rook_moves_bb(sq, board) | get_bishop_moves_bb(sq, board)


# Move generators

def gen_piece_moves(src, board, piece):
    if piece == Piece.PAWN:
        moveset = get_pawn_moves_bb(src, board)
        # Handle promotion moves
        white_promote = src.to_bitboard() & tables.RANKS[Rank.SEVEN] != tables.EMPTY_BB
        black_promote = src.to_bitboard() & tables.RANKS[Rank.TWO] != tables.EMPTY_BB
        if (board.color == Color.WHITE and white_promote) or (board.color == Color.BLACK and black_promote):
            for dest in bitboard.occupied_squares(moveset):
                yield Move(src, dest, Piece.QUEEN)
                yield Move(src, dest, Piece.ROOK)
                yield Move(src, dest, Piece.KNIGHT)
                yield Move(src, dest, Piece.BISHOP)
            return
    elif piece == Piece.KNIGHT:
        moveset = get_knight_moves_bb(src, board)
    elif piece == Piece.BISHOP:
        moveset = get_bishop_moves_bb(src, board)
    elif piece == Piece.ROOK:
        moveset = get_rook_moves_bb(src, board)
    elif piece == Piece.QUEEN:
        moveset = get_queen_moves_bb(src, board)
    elif piece == Piece.KING:
        moveset = get_king_moves_bb(src, board)
    else:
        # This should never happen
        raise RuntimeError("Invalid piece: %s" % str(piece))

    # Handle non-promotion moves
    for dest in bitboard.occupied_squares(moveset):
        yield Move(src, dest)


def gen_moves(board):
    # NOTE: generates pseudo-legal moves
    for piece in Piece:
        piece_bb = board.get_piece_bb(piece)
        for src in bitboard.occupied_squares(piece_bb):
            yield from gen_piece_moves(src, board, piece)


def gen_legal_moves(board):
    return itertools.filterfalse(lambda m: leaves_in_check(board, m), gen_moves(board))

def leaves_in_check(board, move):
    """
    Applies move to board and returns True iff king is left in check

    Uses symmetry of attack e.g. if white knight attacks black king, then black knight on king sq would attack white knight
    So it suffices to look at attacks of various pieces from king sq; if these hit opponent piece of same type then it's check
    """
    board = board.apply_move(move)
    my_color = ~board.color
    my_king_sq = Square(bitboard.lsb_bitscan(board.get_piece_bb(piece.KING, color=my_color)))

    opp_pawns = board.get_piece_bb(piece.PAWN)
    if (tables.PAWN_ATTACKS[my_color][my_king_sq.index] & opp_pawns) != tables.EMPTY_BB: 
        return True

    opp_knights = board.get_piece_bb(piece.KNIGHT)
    if (tables.KNIGHT_MOVES[my_king_sq.index] & opp_knights) != tables.EMPTY_BB:
        return True

    opp_king = board.get_piece_bb(piece.KING)
    if (tables.KING_MOVES[my_king_sq.index] & opp_king) != tables.EMPTY_BB:
        return True

    opp_bishops = board.get_piece_bb(piece.BISHOP)
    opp_queens = board.get_piece_bb(piece.QUEEN)
    bishop_moves = (get_diag_moves_bb(my_king_sq.index, board.combined_all)
            ^ get_antidiag_moves_bb(my_king_sq.index, board.combined_all))
    if (bishop_moves & (opp_bishops | opp_queens)) != tables.EMPTY_BB:
        return True

    opp_rooks = board.get_piece_bb(piece.ROOK)
    rook_moves = (get_rank_moves_bb(my_king_sq.index, board.combined_all)
            ^ get_file_moves_bb(my_king_sq.index, board.combined_all))
    if (rook_moves & (opp_rooks | opp_queens)) != tables.EMPTY_BB:
        return True

    return False
