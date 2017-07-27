import numpy as np

from constants import Rank, File

class Square(object):
    def __init__(self, index):
        self.sq = np.uint8(index)

    @classmethod
    def fromPosition(cls, r, f):
        return cls((r.value<<3) | f.value) # 8*rank + file

