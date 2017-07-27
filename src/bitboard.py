import numpy as np
from square import Square

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

EMPTY_BB = np.uint64(0)

# Clever bit manipulation wizardry to count trailing zeros
# See https://www.chessprogramming.wikispaces.com/BitScan#Bitscan forward-De Bruijn Multiplication-With Isolated LS1B
# NOTE: only works if bb is non-zero
lookup = np.array(
        [ 0,  1, 48,  2, 57, 49, 28,  3,
         61, 58, 50, 42, 38, 29, 17,  4,
         62, 55, 59, 36, 53, 51, 43, 22,
         45, 39, 33, 30, 24, 18, 12,  5,
         63, 47, 56, 27, 60, 41, 37, 16,
         54, 35, 52, 21, 44, 32, 23, 11,
         46, 26, 40, 15, 34, 20, 31, 10,
         25, 14, 19,  9, 13,  8,  7,  6],
        dtype=np.uint8)
debruijn = np.uint64(0x03f79d71b4cb0a89)
def lsb_bitscan(bb):
    return lookup[((bb & -bb) * debruijn) >> 58]

def from_square(sq):
    return np.uint64(1) << sq.index

def clear_square(sq):
    pass

def set_square(sq):
    pass

# Generator that returns corresponding square for each bit set in the bitboard
def occupied_squares(bb):
    while bb != EMPTY_BB:
        lsb_square = Square(lsb_bitscan(bb))
        yield lsb_square
        bb ^= from_square(lsb_square)

# Counts number of bits set using Kernighan's way
# (may want to replace this with faster method)
def pop_count(bb):
    count = np.uint8(0)
    while bb != EMPTY_BB:
        count += np.uint8(1)
        bb &= bb - np.uint64(1)
    return count







