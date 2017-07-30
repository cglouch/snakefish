import numpy as np

import bitboard
from square import Square
from constants import Rank, File, Color

"""
This file contains various pre-computed bitboards and bitboard tables for move generation and general use
"""
EMPTY_BB = np.uint64(0)

RANKS = np.array(
            [np.uint64(0x00000000000000FF) << np.uint8(8*i) for i in range(8)],
            dtype=np.uint64)
FILES = np.array(
            [np.uint64(0x0101010101010101) << np.uint8(i) for i in range(8)],
            dtype=np.uint64)

RANK_MASKS = np.fromiter(
        (RANKS[i//8] for i in range(64)),
        dtype=np.uint64,
        count=64)

FILE_MASKS = np.fromiter(
        (FILES[i%8] for i in range(64)),
        dtype=np.uint64,
        count=64)

A1H8_DIAG = np.uint64(0x8040201008040201)
H1A8_ANTIDIAG = np.uint64(0x0102040810204080)

def compute_diag_mask(i):
    diag = 8*(i & 7) - (i & 56)
    north = -diag & (diag >> 31)
    south = diag & (-diag >> 31)
    return (A1H8_DIAG >> np.uint8(south)) << np.uint8(north)

DIAG_MASKS = np.fromiter(
        (compute_diag_mask(i) for i in range(64)),
        dtype=np.uint64,
        count=64)

def compute_antidiag_mask(i):
    diag = 56 - 8*(i & 7) - (i & 56)
    north = -diag & (diag >> 31)
    south = diag & (-diag >> 31)
    return (H1A8_ANTIDIAG >> np.uint8(south)) << np.uint8(north)

ANTIDIAG_MASKS = np.fromiter(
        (compute_antidiag_mask(i) for i in range(64)),
        dtype=np.uint64,
        count=64)



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

# PAWN QUIETS
# NOTE: MUST BE CHECKED LATER FOR BLOCKERS IN EVENT OF DOUBLE ADVANCE

def compute_pawn_quiet_moves(color, i):
    shift_forward = lambda bb, color, i:  \
        bb << np.uint(8*i) if color == Color.WHITE else bb >> np.uint8(8*i)
    starting_rank = RANKS[Rank.TWO] if color == Color.WHITE else RANKS[Rank.SEVEN]

    sq = Square(i)
    bb = sq.to_bitboard()

    s1 = shift_forward(bb, color, 1)
    s2 = shift_forward((bb & starting_rank), color, 2)

    return s1 | s2

PAWN_QUIETS = np.fromiter(
        (compute_pawn_quiet_moves(color, i)
            for color in Color 
            for i in range(64)),
        dtype=np.uint64,
        count=2*64)
PAWN_QUIETS.shape = (2,64)

# PAWN ATTACKS

def compute_pawn_attack_moves(color, i):
    sq = Square(i)
    bb = sq.to_bitboard()

    if color == Color.WHITE:
        s1 = (bb & ~FILES[File.A]) << np.uint8(7)
        s2 = (bb & ~FILES[File.H]) << np.uint8(9)
    else:
        s1 = (bb & ~FILES[File.A]) >> np.uint8(9)
        s2 = (bb & ~FILES[File.H]) >> np.uint8(7)

    return s1 | s2

PAWN_ATTACKS = np.fromiter(
        (compute_pawn_attack_moves(color, i)
            for color in Color 
            for i in range(64)),
        dtype=np.uint64,
        count=2*64)
PAWN_ATTACKS.shape = (2,64)

# FIRST RANK MOVES
# Array is indexed by file of square and occupancy of line

def compute_first_rank_moves(i, occ):
    # i is square index from 0 to 8
    # occ is 8-bit number that represents occupancy of the rank 
    # Returns first rank moves (as uint8)

    left_ray = lambda x: x | (x - np.uint8(1))
    right_ray = lambda x: x | ~(x - np.uint8(1))

    x = np.uint8(1) << np.uint8(i)
    occ = np.uint8(occ)

    left_attacks = left_ray(x)
    left_blockers = left_attacks & occ
    if left_blockers != EMPTY_BB:
        leftmost = np.uint8(1) << bitboard.msb_bitscan(np.uint64(left_blockers))
        left_garbage = left_ray(leftmost)
        left_attacks ^= left_garbage

    right_attacks = right_ray(x)
    right_blockers = right_attacks & occ
    if right_blockers != EMPTY_BB:
        rightmost = np.uint8(1) << bitboard.lsb_bitscan(np.uint64(right_blockers))
        right_garbage = right_ray(rightmost)
        right_attacks ^= right_garbage

    return left_attacks ^ right_attacks



FIRST_RANK_MOVES = np.fromiter(
        (compute_first_rank_moves(i, occ)
            for i in range(8) # 8 squares in a rank 
            for occ in range(256)), # 2^8 = 256 possible occupancies of a rank
        dtype=np.uint8,
        count=8*256)
FIRST_RANK_MOVES.shape = (8,256)
