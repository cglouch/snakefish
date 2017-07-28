import numpy as np

from square import Square
from constants import Rank, File, Color

"""
This file contains various pre-computed bitboards for move generation and general use
"""

RANKS = np.array(
            [np.uint64(0x0000000000000011) << np.uint8(8*i) for i in range(8)],
            dtype=np.uint64)
FILES = np.array(
            [np.uint64(0x0101010101010101) << np.uint8(i) for i in range(8)],
            dtype=np.uint64)

A1H8_DIAG = np.uint64(0x8040201008040201)
H1A8_ANTIDIAG = np.uint64(0x0102040810204080)

# Bitboards for move generation


# KING

def compute_king_moves(i):
    sq = Square(i)
    bb = sq.to_bitboard()

    nw = (bb & ~FILES[File.A]) << np.uint8(7)
    n  = bb << np.uint8(8)
    ne = (bb & ~FILES[File.H]) << np.uint8(9)
    e  = (bb & ~FILES[File.H]) << np.uint8(1)
    se = (bb & ~FILES[File.H]) >> np.uint8(7)
    s  = bb >> np.uint8(8)
    sw = (bb & ~FILES[File.A]) >> np.uint8(9)
    w  = (bb & ~FILES[File.A]) >> np.uint8(1)

    return nw | n | ne | e | se | s | sw | w

KING_MOVES = np.fromiter(
        (compute_king_moves(i) for i in range(64)),
        dtype=np.uint64,
        count=64)

# KNIGHT 

def compute_knight_moves(i):
    sq = Square(i)
    bb = sq.to_bitboard()

    m1 = ~(FILES[File.A] | FILES[File.B])
    m2 = ~FILES[File.A]
    m3 = ~FILES[File.H]
    m4 = ~(FILES[File.H] | FILES[File.G])

    s1 = (bb & m1) << np.uint8(6)
    s2 = (bb & m2) << np.uint8(15)
    s3 = (bb & m3) << np.uint8(17)
    s4 = (bb & m4) << np.uint8(10)
    s5 = (bb & m4) >> np.uint8(6)
    s6 = (bb & m3) >> np.uint8(15)
    s7 = (bb & m2) >> np.uint8(17)
    s8 = (bb & m1) >> np.uint8(10)

    return s1 | s2 | s3 | s4 | s5 | s6 | s7 | s8


KNIGHT_MOVES = np.fromiter(
        (compute_knight_moves(i) for i in range(64)),
        dtype=np.uint64,
        count=64)

# PAWN

def compute_pawn_quiet_moves(color, i):
    pass

def compute_pawn_attack_moves(color, i):
    pass

PAWN_MOVES = np.fromiter(
        (compute_pawn_quiet_moves(i) | compute_pawn_attack_moves(i) 
            for color in Color 
            for i in range(64)),
        dtype=np.uint64,
        count=2*64)
PAWN_MOVES.shape =  (2,64)

