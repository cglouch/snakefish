import numpy as np

import bitboard

def test_bitscan():
    assert bitboard.lsb_bitscan(np.uint64(0xF000000000000000)) == np.uint8(60)
    assert bitboard.msb_bitscan(np.uint64(0xF000000000000000)) == np.uint8(63)

def test_popcount():
    assert bitboard.pop_count(np.uint64(0xF0000F00000F0000)) == np.uint8(12)
