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


The second approach to board representation is **piece-centric**. Instead of describing the contents of the squares, we describe the locations of the pieces. There's a variety of ways to do this, but the most ingenious (and thankfully also the most efficient!) is to use **bitboards**. Bitboards take advantage of the convenient fact that chess boards have 64 squares and that modern processors are particularly good at manipulating 64 bit quantities. If we decide on a mapping of bit positions to squares, then we can easily represent the locations of a given piece type as a single 64 bit quantity: a 1 in a bit represents the presence of that piece type in the corresponding square, and a 0 represents its absence. 


Note that we can't represent all of the pieces on a single bitboard - a bit can only encode 2 values but we have 12 piece types (13 including empty). Instead what we do is define individual bitboards for each piece type: white king, black king, white pawns, black pawns, etc. For convenience sake, we also maintain some combined bitboards that show up often in computations. Our board class ends up looking like this:

```python
class ChessBoard(object):
    def __init__(self):
        self.pieces = np.zeros((2,6), dtype=np.uint64) # 2 sides, 6 piece bitboards per side
        self.combined_side = np.zeros(2, dtype=np.uint64) # Combined bitboard for all pieces of given side
        self.combined_all = np.uint64(0) # Combined bitboard for all pieces on the board
        self.to_move = Color.WHITE
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

As for the definition of a piece, we'll use a simple enum. This isn't particularly interesting so we'll omit it here. We now have enough to define a move:

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

Great! So how do we actually generate these moves? 

todo: describe knight attacks computation in detail, this showcases the power of bitboards. instead of having to perform 8 checks to see if each knight attack square contains a same-colored piece, we can do the whole computation in a single bitwise and operation. We're exploiting the parallel nature of bitwise operations to compute the set intersection that we're interested in. Of course, in order to enumerate the actual moves we'll still need to perform some iteration, but we've saved ourselves the trouble of 


### Evaluation

describe evaluation

evaluation is another area where bitboard approach shines. Since engine needs to assign score to a lot of positiions, we want quick way of determining various heuristics on the board. bitboards allow us to do so


### Search

Chess has a [branching factor](https://en.wikipedia.org/wiki/Branching_factor) of ~35

## Tests




## Resources

chessprogrammingwiki  
stockfish  
wisc edu page  
rust move gen lib  
chess engine in c amazon redshift  
