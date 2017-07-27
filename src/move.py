class Move(object):
    def __init__(self, src, dest, promo=None):
        """
        src is Square representing source square
        dst is Square representing destination square
        promo is Piece representing promotion
        """
        self.src = src
        self.dest = dest
        self.promo = promo

    def __str__(self):
        if self.promo:
            return "%s -> %s = %s" % (str(self.src), str(self.dest), str(self.promo))
        else:
            return "%s -> %s" % (str(self.src), str(self.dest))


