import numpy as np

from constants import Rank, File

class Square(object):
    def __init__(self, index):
        self.index = np.uint8(index)

    def __str__(self):
        r = self.index // 8
        f = self.index % 8
        return "%s%d" % (chr(ord('A')+f), 1+r)

    @classmethod
    def from_position(cls, r, f):
        return cls((r.value << np.uint8(3)) | f.value) # 8*rank + file

    def to_bitboard(self):
        return np.uint64(1) << self.index

