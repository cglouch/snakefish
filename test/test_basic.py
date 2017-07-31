import numpy as np

import bitboard

def test_bitscan():
    assert bitboard.lsb_bitscan(np.uint64(0xF000000000000000)) == np.uint8(60)
