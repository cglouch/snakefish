<img align="right" width="45" height="45" src="https://i.imgur.com/d6zOkdQ.png">

# Snakefish
A chess engine created from scratch in Python

## Overview
Snakefish uses a bitboard approach to represent the state of the chess board and to generate possible moves. Search is performed using the negamax algorithm with a simple heuristic. The name is a play on "Stockfish", a well known chess engine (and "snake", cause, you know, Python).

Check out a sample game I played against Snakefish here! 


## Chess engine basics

There are four main components to a chess engine:

- Board representation
- Move generation
- Evaluation
- Search

We will give an overview of these components and describe how they're implemented in Snakefish.

### Board representation

The first decision one makes when writing a chess engine is deciding on a board representation.  Because engines need to analyze a huge number of positions, we want to choose a board representation that allows for efficient move generation, fast evaluation, and minimal memory footprint. No small task!

Two approaches come to mind for representing a chess board. The most intuitive is the **square-centric** representation, in which we describe the board in terms of the contents of its 64 squares. The natural approach might be to use a 8x8 2D array to represent the squares of the board, where each entry corresponds to the piece on that square. So the starting position would look like:

```python
board = [
    r, n, b, q, k, b, n, r,
    p, p, p, p, p, p, p, p,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    P, P, P, P, P, P, P, P,
    R, N, B, Q, K, B, N, R]
```

where the letters are placeholders for the pieces, which could be represented as classes, enums, ints, or whatever.


The second approach to board representation - and the one we'll use - is **piece-centric**. Instead of describing the contents of the squares, we describe the locations of the pieces. There's a variety of ways to do this, but the most ingenious (and thankfully also the most efficient!) is to use **bitboards**. Bitboards take advantage of the convenient fact that chess boards have 64 squares and that modern processors are particularly good at manipulating 64 bit quantities. If we decide on a mapping of bit positions to squares, then we can easily represent the locations of a given piece type as a single 64 bit quantity: a 1 in a bit represents the presence of that piece type in the corresponding square, and a 0 represents its absence. 


Note that we can't represent all of the pieces on a single bitboard - a bit can only encode 2 values but we have 12 piece types (13 including empty). Instead what we do is define individual bitboards for each piece type: white king, black king, white pawns, black pawns, etc. For convenience sake, we also maintain some combined bitboards that show up often in computations. Our board class ends up looking like this:

```python
class ChessBoard(object):
    def __init__(self):
        self.pieces = np.zeros((2,6), dtype=np.uint64) # 2 sides, 6 piece bitboards per side
        self.combined_color = np.zeros(2, dtype=np.uint64) # Combined bitboard for all pieces of given color
        self.combined_all = np.uint64(0) # Combined bitboard for all pieces on the board
        self.color = Color.WHITE # Color to move
        ...
```

Here's what the bitboards look like visually at the beginning of a game:

![Beginning](http://chessprogramming.wikispaces.com/file/view/bitboard.gif/158504035/bitboard.gif)

Our implementation maps squares to bits as described [here](https://github.com/cglouch/snakefish/blob/16f1e9f893af3e43d96ed3d20f122527aa327348/src/bitboard.py#L7-L19). For instance in the image above, the white pawns bitboard would be the 64-bit value `0b0000000000000000000000000000000000000000000000001111111100000000`.

#### So what's the point?

Good question! At first bitboards seem like a perplexing choice. Why go through all this trouble just to define the board? Well as alluded to earlier, the big win for bitboards is efficiency. With a bit of cleverness (pardon the pun), we can express most of the computations we need to perform in terms of bitwise operations. This effectively "parallelizes" the computations, and drastically cuts down on the number of instructions needed to generate moves - a major bottleneck for a chess engine. Moreover, bitboards are fairly compact in terms of memory usage. While there's no shortage of RAM these days, a low memory footprint still helps fit more data into cache, which is important for performance. 

Let's take a look at move generation to see some examples of bitboards in action.

### Move generation

Arguably the hardest part of a chess engine is generating moves quickly and correctly. We'll need to leverage the power of bitboards in order to do so. The first step is of course to describe a move. A move requires 3 fields: a source square, a destination square, and an optional promotion piece (in the event of a pawn reaching the end of the board). If we wanted to, we could use a bitboard with a single bit set to represent a square; however, we'll define a separate square class for reasons that will be revealed later:

```python
class Square(object):
    def __init__(self, index):
        self.index = np.uint8(index)
```

A square simply stores an index from 0 to 63. Note that given a square, we can trivially convert it to a bitboard via shifting left by the index. Moreover, given a bitboard, we can get the square representing the least significant bit with [some clever bit twiddling](https://github.com/cglouch/snakefish/blob/31764a496b93f64a9a88751144faca9e6f9603f4/src/bitboard.py#L23-L38). This will come in handy.

As for the definition of a piece, we'll use a simple enum:

```python
class Piece(IntEnum):
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5
```

We now have enough to define a move:

```python
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
```

Great! So how do bitboards fit into this? The key insight is that we can use a bitboard to encode the places that a piece can move from a given square. I'll call this a *moveset*. A moveset bitboard will have 1's on squares that the piece can move to, and 0's everywhere else. 

#### Example - non-sliding piece

For instance, let's say we want to calculate the moveset of a white king on B2. The white king bitboard would be:

```
wk = 0b0000000000000000000000000000000000000000000000000000001000000000
```

Visually this corresponds to:
```
0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0
0 1 0 0 0 0 0 0
0 0 0 0 0 0 0 0
```

A king can move one square in any direction, which we can represent by shifting the bit pattern an appropriate amount. For instance, the square to the left of the king is given by `wk >> 1` (remember that the bit positions increase in significance as we move on the board from left to right, bottom to top; so to get the left of a square we need to shift the bit pattern right). The square above and to the left is `wk << 7`, the square above is `wk << 8`, etc. There's a catch, however, which is that if the king was on say A2, then there is no square to the left it can move to, but our bitshifting approach would mistakenly yield the bitboard for H1. To fix this, we can use a mask to zero out files A and H whenever we're calculating squares that lie to the left or right, respectively. Note that this clipping effect only applies to the files; we don't need to worry about the ranks at the top or bottom because shifting too far up or down will correctly zero out the bit pattern on its own. To summarize:

```python
# fileA_bb is bitboard with 1's on the A file and 0's elsewhere
# fileH_bb is bitboard with 1's on the H file and 0's elsewhere
# wk is bitboard with 1 where white king is and 0 elsewhere

nw = (wk & ~fileA_bb) << 7 
n  = wk << 8
ne = (wk & ~fileH_bb) << 9 
e  = (wk & ~fileH_bb) << 1 
se = (wk & ~fileH_bb) >> 7
s  = wk >> 8
sw = (wk & ~fileA_bb) >> 9 
w  = (wk & ~fileA_bb) >> 1
```

So where can the white king move? Well, it can move to any of the surrounding squares as long as a) it's not putting itself into check, and b) the square isn't occupied by a white piece. Let's ignore checks for now (we'll deal with those later). Then describing the moveset of the king is simple:

```python
# combined_white is bitboard with 1's for squares occupied by white piece, 0 elsewhere
wk_moves_bb = nw | n | ne | e | se | s | sw | w
wk_moves_bb &= ~combined_white
```

At this point we notice that with the exception of the last line, this computation is the same any time we calculate the moveset of a king on a given square. Since a chess board has only 64 squares, we might as well just compute the king moveset bitboard for each square at the beginning of the program and store the results in a table. Then any time we want a king's moveset from a given square, it's as simple as looking up the appropriate bitboard in the pre-computed table and doing a bitwise AND with the bitwise NOT of the current color's combined pieces. (This is why we chose to define a Square class; it gives us an easy way to index into the table). Here's the code:

```python
def get_king_moves_bb(src, board):
    # src is Square where king is
    # board is the current ChessBoard
    return tables.KING_MOVES[src.index] & ~board.combined_color[board.color] #TODO: make this right part a function
    #TODO maybe make an array of these functions if they have the same signature, then define gen_moves_one_piece
```

This example showcases the power of bitboards. With a naive square-centric approach, we would need to perform 8 separate checks to see whether the king's potential destination squares were currently occupied by same-colored pieces. However, with bitboards, these checks can be performed simultaneously in a single bitwise AND instruction. We're exploiting the parallel nature of bitwise operations to compute the set intersection that we're interested in. Of course in order to generate the actual moves, we do need to iterate through the squares set in the resulting bitboard, but it's still preferable to the naive square-centric approach because during this iteration we no longer need to check for intersection - that's already been taken care of by the bitwise AND. The beauty of the bitboard approach is its ability to perform these sorts of calculations so quickly and concisely.

With a couple tweaks, we can use the method described above to calculate the movesets for the pawns and the knights as well. Kings, pawns, and knights are all similar in that they're *non-sliding* pieces. From a computational perspective, these are nice because their movement really only depends on the source square and whether or not the destination square is occupied by a same-colored piece. This means that we can compute their movesets easily with a lookup based on the piece's square followed by a simple bitwise AND.

#### Example - sliding pieces

Sliding pieces (bishop, rook, and queen) pose a greater challenge. This is because the occupancy of the board affects the movement of the sliding piece, as shown in the image below:

![Sliding](http://i.imgur.com/4aTSjVR.png)

Thus we can't simply lookup the movement based on the square alone as we did for non-sliders; we need a way to take the board's occupancy into account as well. The immediate thought that comes to mind is to create a 2D table: one row for each square and one column for each possible occupancy state. Unfortunately a back of the envelope calculation shows this is infeasible: there are 64 squares, 2^64 possible occupancies, and 8 bytes required to store a bitboard, meaning the table size would be 2^73 bytes ≈ 9 * 10^9 TB. This is obviously much too large. We need a way to limit the occupancy space so we can index into a smaller table. 

Two key observations:  
* If we're trying to, say, calculate the horizontal movements of a rook on E4, then we really only care about the occupancy of the fourth rank. A similar claim holds for vertical, diagonal, and anti-diagonal movements: we only care about the occupancy of the lines that the square is on.

* We can use a combination of integer multiplication and bit shifting to map any pattern along a rank, file, diagonal, or anti-diagonal to the same pattern along the first rank, and vice versa. This process is described [here](http://chessprogramming.wikispaces.com/Flipping+Mirroring+and+Rotating#Rank,%20File%20and%20Diagonal). For instance, here's how we can rotate the A file to the first rank:
![Rotation](https://i.imgur.com/T9CPHGj.png)

These observations motivate an approach for calculating sliding piece moves called *Kindergarten bitboards*. 

#### Putting it all together

We now have a way of encoding the moveset bitboard of any given piece on any given square. But we still haven't generated the actual moves. How do we do that? Fittingly enough, we can use Python generators. We'll take it piece by piece. For each piece bitboard, we'll isolate the occupied squares. For each square, we'll compute the bitboard moveset of the piece on that source square. Finally, we'll generate a move from the source square to each destination square in the moveset.


### Evaluation

describe evaluation

evaluation is another area where bitboard approach shines. Since engine needs to assign score to a lot of positions, we want quick way of determining various heuristics on the board. bitboards allow us to express many of these heuristics as simple bitwise operations 

consider problem of assessing how many pieces are in center of board - this is a heuristic we're probably interested in. With bitboards, this is easy to compute! Just take the bitwise and of our combined pieces and the bitboard representing the center of the board; then count the number of 1s set. 


### Search

Chess has a [branching factor](https://en.wikipedia.org/wiki/Branching_factor) of ~35

## Tests




## Resources

chessprogrammingwiki  
stockfish  
wisc edu page  
rust move gen lib  
chess engine in c amazon redshift  
