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
    # Returns first rank moves (as uint64 bitboard)

    occ = np.uint64(occ)

    # This looks backwards because of the board representation!
    left_mask = lambda x: x - np.uint64(1)
    right_mask = lambda x: ~(x | (x - np.uint64(1)))

    # Example (only first row shown):
    # ...1.... = x 
    # ....1111 = right_mask(x)
    # 111..... = left_mask(x)

    x = Square(i).to_bitboard()
    left_occ = occ & left_mask(x)
    right_occ = occ & right_mask(x)

    left_blocker = Square(0).to_bitboard()
    right_blocker = Square(7).to_bitboard()
    if left_occ != EMPTY_BB:
        left_blocker = Square(bitboard.lsb_bitscan(left_occ)).to_bitboard()
    if right_occ != EMPTY_BB:
        right_blocker = Square(bitboard.msb_bitscan(right_occ)).to_bitboard()

    # Example (only first row shown)
    # .1...... = left_blocker
    # .....1.. = right_blocker

    # .1111111 = left_blocker | right_mask(left_blocker)
    # 111111.. = right_blocker | left_mask(right_blocker)

    # .11111.. = result

    result = (left_blocker | right_mask(left_blocker)) & (right_blocker | left_mask(right_blocker))
    result &= RANKS[Rank.ONE] # Isolate first rank

    #TODO: maybe change this to 8-bit version since we don't need the row duplication

    """
    # At this point first rank of result holds moveset for given square and occupancy
    # We finish off by copying this pattern to the other ranks

    result |= result << np.uint8(8)
    result |= result << np.uint8(16)
    result |= result << np.uint8(32)
    """

    return result


FIRST_RANK_MOVES = np.fromiter(
        (compute_first_rank_moves(i, occ)
            for i in range(8) # 8 squares in a rank 
            for occ in range(256)), # 2^8 = 256 possible occupancies of a rank
        dtype=np.uint64,
        count=8*256)
FIRST_RANK_MOVES.shape = (8,256)
