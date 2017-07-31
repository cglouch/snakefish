import numpy as np
from square import Square
from constants import Rank, File

"""
This file contains a variety of functions for manipulating bitboards (represented using uint64 in numpy)

Note that we use a little-endian rank-file mapping, i.e.:

56 57 58 59 60 61 62 63         A8 B8 C8 D8 E8 F8 G8 H8
48 49 50 51 52 53 54 55         A7 B7 C7 D7 E7 F7 G7 H7
40 41 42 43 44 45 46 47         A6 B6 C6 D6 E6 F6 G6 H6
32 33 34 35 36 37 38 39    =    A5 B5 C5 D5 E5 F5 G5 H5
24 25 26 27 28 29 30 31         A4 B4 C4 D4 E4 F4 G4 H4
16 17 18 19 20 21 22 23         A3 B3 C3 D3 E3 F3 G3 H3
 8  9 10 11 12 13 14 15         A2 B2 C2 D2 E2 F2 G2 H2
 0  1  2  3  4  5  6  7         A1 B1 C1 D1 E1 F1 G1 H1

where least to most significant bit ranges from 0 to 63.
"""

# May want to move this to tables.py
EMPTY_BB = np.uint64(0)

# Clever bit manipulation wizardry to count trailing/leading zeros
# See https://www.chessprogramming.wikispaces.com/BitScan#Bitscan forward-De Bruijn Multiplication-With Isolated LS1B
# NOTE: only works if bb is non-zero
debruijn = np.uint64(0x03f79d71b4cb0a89)

lsb_lookup = np.array(
        [ 0,  1, 48,  2, 57, 49, 28,  3,
         61, 58, 50, 42, 38, 29, 17,  4,
         62, 55, 59, 36, 53, 51, 43, 22,
         45, 39, 33, 30, 24, 18, 12,  5,
         63, 47, 56, 27, 60, 41, 37, 16,
         54, 35, 52, 21, 44, 32, 23, 11,
         46, 26, 40, 15, 34, 20, 31, 10,
         25, 14, 19,  9, 13,  8,  7,  6],
        dtype=np.uint8)

msb_lookup = np.array(
        [ 0, 47,  1, 56, 48, 27,  2, 60,
         57, 49, 41, 37, 28, 16,  3, 61,
         54, 58, 35, 52, 50, 42, 21, 44,
         38, 32, 29, 23, 17, 11,  4, 62,
         46, 55, 26, 59, 40, 36, 15, 53,
         34, 51, 20, 43, 31, 22, 10, 45,
         25, 39, 14, 33, 19, 30,  9, 24,
         13, 18,  8, 12,  7,  6,  5, 63],
        dtype=np.uint8)

def lsb_bitscan(bb):
    return lsb_lookup[((bb & -bb) * debruijn) >> np.uint8(58)]

def msb_bitscan(bb):
    bb |= bb >> np.uint8(1)
    bb |= bb >> np.uint8(2)
    bb |= bb >> np.uint8(4)
    bb |= bb >> np.uint8(8)
    bb |= bb >> np.uint8(16)
    bb |= bb >> np.uint8(32)
    return msb_lookup[(bb * debruijn) >> np.uint8(58)]


# Generator that returns corresponding square for each bit set in the bitboard
def occupied_squares(bb):
    while bb != EMPTY_BB:
        lsb_square = Square(lsb_bitscan(bb))
        yield lsb_square
        bb ^= lsb_square.to_bitboard()

# Counts number of bits set using Kernighan's way
# (may want to replace this with faster method)
def pop_count(bb):
    count = np.uint8(0)
    while bb != EMPTY_BB:
        count += np.uint8(1)
        bb &= bb - np.uint64(1)
    return count

def is_set(bb, sq):
    return (sq.to_bitboard() & bb) != EMPTY_BB

def to_str(bb):
    bb_str = []
    for r in reversed(Rank):
        for f in File:
            sq = Square.from_position(r, f)
            if is_set(bb, sq):
                bb_str.append('1')
            else:
                bb_str.append('.')
        bb_str.append('\n')
    return ''.join(bb_str)

def clear_square(bb, sq):
    return (~sq.to_bitboard()) & bb

def set_square(bb, sq):
    return sq.to_bitboard() | bb
