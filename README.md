# Snakefish
A chess engine created from scratch in Python

## Overview
Snakefish uses a bitboard approach to represent the state of the chess board and to generate possible moves. Search is performed using the negamax algorithm with a simple heuristic. The name is a play on "Stockfish", a well known chess engine (and "snake", cause, you know, Python).

Check out a sample game I (white) played against Snakefish (black):

<p align="center">
  <img src="https://i.imgur.com/L9evkOR.gif">
</p>

You can see the engine plays okay up until the midgame when it loses its queen to a discovered check. This was caused by a combination of shallow search depth and the horizon effect, which we'll discuss later. Nonetheless, the engine usually does manage to win against weaker players (sorry Dad!).

Note that I haven't implemented castling or en passant moves yet, as these complicate the code and are a bit of a hassle to get working. My description will pretend these moves don't exist. Eventually I'll try to add them in.

I chose to write this in Python since it was more of a learning exercise than an attempt at a competitive engine. Obviously the downside of Python for something performance intensive is that it's pretty slow. If I were making a serious engine I would likely rewrite it in something like C++. That said, using Python was an interesting challenge since I had to really pay attention to efficiency to even search up to a shallow depth. 

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

Our implementation maps squares to bits as described [here](https://github.com/cglouch/snakefish/blob/1a78680e604aea0158e8ec121fee57219b72a79a/src/bitboard.py#L8-L19). For instance in the image above, the white pawns bitboard would be the 64-bit value `0b0000000000000000000000000000000000000000000000001111111100000000`.

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

A square simply stores an index from 0 to 63. Note that given a square, we can trivially convert it to a bitboard via shifting left by the index. Moreover, given a bitboard, we can get the square representing the least significant bit with [some clever bit twiddling](https://github.com/cglouch/snakefish/blob/1a78680e604aea0158e8ec121fee57219b72a79a/src/bitboard.py#L25-L62). This will come in handy.

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

#### Non-sliding pieces

For instance, let's say we want to calculate the moveset of a white king on B2. The white king bitboard would be:

```
wk = 0b0000000000000000000000000000000000000000000000000000001000000000
```

Visually this corresponds to:
```
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. 1 . . . . . .
. . . . . . . .
```
(For readability, we'll use '.' instead of '0' when representing bitboards.)

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
    return tables.KING_MOVES[src.index] & ~board.combined_color[board.color]
```

This example showcases the power of bitboards. With a naive square-centric approach, we would need to perform 8 separate checks to see whether the king's potential destination squares were currently occupied by same-colored pieces. However, with bitboards, these checks can be performed simultaneously in a single bitwise AND instruction. We're exploiting the parallel nature of bitwise operations to compute the set intersection that we're interested in. Of course in order to generate the actual moves, we do need to iterate through the squares set in the resulting bitboard. However, it's still preferable to the naive square-centric approach because during this iteration we no longer need to check for intersection - that's already been taken care of by the bitwise AND. The beauty of the bitboard approach is its ability to perform these sorts of calculations so quickly and concisely.

With a couple tweaks, we can use the method described above to calculate the movesets for the pawns and the knights as well. Kings, pawns, and knights are all similar in that they're *non-sliding* pieces. From a computational perspective, these are nice because their movement really only depends on the source square and whether or not the destination square is occupied by a same-colored piece. This means that we can compute their movesets easily with a lookup based on the piece's square followed by a simple bitwise AND.

#### Sliding pieces

Sliding pieces (bishop, rook, and queen) pose a greater challenge. This is because the occupancy of the board affects the movement of the piece, as shown in the image below:

![Sliding](http://i.imgur.com/4aTSjVR.png)

Thus we can't simply lookup the movement based on the square alone as we did for non-sliders; we need a way to take the board's occupancy into account as well. The immediate thought that comes to mind is to create a 2D table: one row for each square and one column for each possible occupancy state. Unfortunately a back of the envelope calculation shows this is infeasible: there are 64 squares, 2^64 possible occupancies, and 8 bytes required to store a bitboard, meaning the table size would be 2^73 bytes ≈ 9 * 10^9 TB. This is obviously much too large. We need a way to limit the occupancy space so we can index into a smaller table. 

Two key observations:  
* If we're trying to, say, calculate the horizontal movements of a rook on E4, then we really only care about the occupancy of the fourth rank. A similar claim holds for vertical, diagonal, and anti-diagonal movements: we only care about the occupancy of the lines that the square is on.

* We can use a combination of integer multiplication and bit shifting to map any pattern along a rank, file, diagonal, or anti-diagonal to the same pattern along the first rank, and vice versa. This process is described [here](http://chessprogramming.wikispaces.com/Flipping+Mirroring+and+Rotating#Rank,%20File%20and%20Diagonal). For instance, here's how we can rotate the A file to the first rank:
![Rotation](https://i.imgur.com/T9CPHGj.png)

These observations motivate an approach for calculating sliding piece moves called *Kindergarten bitboards*. The main idea underlying Kindergarten bitboards is that while it's impossible to store sliding piece movements for the whole board, it is possible if we limit ourselves to the first rank. To that end, we pre-compute a table with dimensions 8 x 2^8: 8 for the squares along the first rank, and 2^8 for the possible first rank occupancies. Each entry of the table stores the horizontal sliding piece moveset of a piece on the given square with the given occupancy. Note that this can easily fit into memory, requiring only 8 * 2^8 * 1 bytes ≈ 2 KB. Now any time we need the moveset for a sliding piece along some line, we can use the integer multiplication process described above to transform this problem into its first rank equivalent. We then look up the pre-computed moveset in the table for the corresponding square and occupancy, and finally we map this moveset back to the original line we were interested in. The name Kindergarten bitboards comes from the integer multiplication process that one learns in school and that we're using here to map lines back and forth to the first rank. (Chess programmers must be particularly precocious though, because I didn't learn this multiplication algorithm until the 3rd grade!)

Kindergarten bitboards are perhaps best understood through an example, so let's see how they work to calculate the vertical movements of the rook shown in this image:

![rook](https://i.imgur.com/o4jrK9O.png?1)

The combined occupancy bitboard is:

```
. . . . . . . .
1 . . . . 1 . .
. . . . . . . . 
1 . . . . . 1 .
. . . . . 1 . .
. . . 1 . . . .
1 . . . . . . .
1 . . . . . . .
```

Since we're only interested in vertical movement, we'll mask the A file, so the occupancy becomes:

```
. . . . . . . .
1 . . . . . . .
. . . . . . . . 
1 . . . . . . .
. . . . . . . .
. . . . . . . .
1 . . . . . . .
1 . . . . . . .
```

We use Kindergarten multiplication (in this case, multiplication by the main diagonal followed by a right shift of 56) to map this occupancy pattern to the first rank:

```
. . . . . . . .      . . . . . . . .
1 . . . . . . .      . . . . . . . .
. . . . . . . .      . . . . . . . .
1 . . . . . . .  =>  . . . . . . . .
. . . . . . . .      . . . . . . . .
. . . . . . . .      . . . . . . . .
1 . . . . . . .      . . . . . . . .
1 . . . . . . .      . 1 . 1 . . 1 1
```

And now we're all set to perform the lookup into the pre-computed table for the first rank. The square index is 3, since that's where the rook got mapped to. The first rank occupancy index that we just calculated is ``0b11001010 = 202``. The corresponding table entry is:

```
FIRST_RANK_MOVES[3][202] = 0b01110110
```

Finally, we map this pattern back to the A file (again via Kindergarten multiplication):

```
. . . . . . . .      . . . . . . . .
. . . . . . . .      1 . . . . . . .
. . . . . . . .      1 . . . . . . .
. . . . . . . .  =>  . . . . . . . .
. . . . . . . .      1 . . . . . . .
. . . . . . . .      1 . . . . . . .
. . . . . . . .      1 . . . . . . .
. 1 1 . 1 1 1 .      . . . . . . . .
```

Voila! The vertical moveset for the rook, as desired. Here's the code for calculating vertical movesets in general:

```python
def get_file_moves_bb(i, occ):
    """
    i is index of square
    occ is the combined occupancy of the board
    """
    f = i & np.uint8(7)
    # Shift to A file
    occ = tables.FILES[File.A] & (occ >> f)
    # Map occupancy and index to first rank
    occ = (tables.A1H8_DIAG * occ) >> np.uint8(56)
    first_rank_index = (i ^ np.uint8(56)) >> np.uint8(3)
    # Lookup moveset and map back to H file
    occ = tables.A1H8_DIAG * tables.FIRST_RANK_MOVES[first_rank_index][occ]
    # Isolate H file and shift back to original file
    return (tables.FILES[File.H] & occ) >> (f ^ np.uint8(7))
```

The functions for diagonal, anti-diagonal, and horizontal movesets are similar, so we'll omit them from this description. Combining these functions appropriately gives us the movesets for rooks, bishops, and queens.


#### Putting it all together

We now have a way of encoding the moveset bitboard of any given piece on any given square. But we still haven't generated the actual moves. How do we do that? Fittingly enough, we can use Python generators. We'll take it piece by piece. For each piece bitboard, we'll isolate the occupied squares. For each square, we'll compute the bitboard moveset of the piece on that source square. Finally, we'll generate a move from the source square to each destination square in the moveset.

```python
def gen_moves(board):
    for piece in Piece:
        piece_bb = board.get_piece_bb(piece)
        for src in bitboard.occupied_squares(piece_bb):
            yield from gen_piece_moves(src, board, piece)

def gen_piece_moves(src, board, piece):
    if piece == Piece.PAWN:
        moveset = get_pawn_moves_bb(src, board)
        # Handle promotion moves
        white_promote = src.to_bitboard() & tables.RANKS[Rank.SEVEN] != tables.EMPTY_BB
        black_promote = src.to_bitboard() & tables.RANKS[Rank.TWO] != tables.EMPTY_BB
        if (board.color == Color.WHITE and white_promote) or (board.color == Color.BLACK and black_promote):
            for dest in bitboard.occupied_squares(moveset):
                yield Move(src, dest, Piece.QUEEN)
                yield Move(src, dest, Piece.ROOK)
                yield Move(src, dest, Piece.KNIGHT)
                yield Move(src, dest, Piece.BISHOP)
            return
    elif piece == Piece.KNIGHT:
        moveset = get_knight_moves_bb(src, board)
    elif piece == Piece.BISHOP:
        moveset = get_bishop_moves_bb(src, board)
    elif piece == Piece.ROOK:
        moveset = get_rook_moves_bb(src, board)
    elif piece == Piece.QUEEN:
        moveset = get_queen_moves_bb(src, board)
    elif piece == Piece.KING:
        moveset = get_king_moves_bb(src, board)
    else:
        # This should never happen
        raise RuntimeError("Invalid piece: %s" % str(piece))

    # Handle non-promotion moves
    for dest in bitboard.occupied_squares(moveset):
        yield Move(src, dest)
```

And we're done! Well, not quite - we still haven't dealt with checks. What we have generated now are called *pseudo-legal moves*; they're the moves that can be made but that potentially leave the king in check. We need to narrow these down to the *legal moves* in which the king is safe. There are a couple approaches for dealing with this, but the easiest is just to examine the state of the board after each pseudo-legal move is made, and filter out any moves that would leave the king in check:

```python
def gen_legal_moves(board):
    return itertools.filterfalse(lambda m: leaves_in_check(board, m), gen_moves(board))

def leaves_in_check(board, move):
    """
    Applies move to board and returns True iff king is left in check
    Uses symmetry of attack e.g. if white knight attacks black king, then black knight on king sq would attack white knight
    So it suffices to look at attacks of various pieces from king sq; if these hit opponent piece of same type then it's check
    """
    board = board.apply_move(move)
    board.color = ~board.color
    my_king_sq = Square(bitboard.lsb_bitscan(board.get_piece_bb(Piece.KING)))

    opp_color = ~board.color
    opp_pawns = board.get_piece_bb(Piece.PAWN, color=opp_color)
    if (tables.PAWN_ATTACKS[board.color][my_king_sq.index] & opp_pawns) != tables.EMPTY_BB: 
        return True

    opp_knights = board.get_piece_bb(Piece.KNIGHT, color=opp_color)
    if (get_knight_moves_bb(my_king_sq, board) & opp_knights) != tables.EMPTY_BB:
        return True

    opp_king = board.get_piece_bb(Piece.KING, color=opp_color)
    if (get_king_moves_bb(my_king_sq, board) & opp_king) != tables.EMPTY_BB:
        return True

    opp_bishops = board.get_piece_bb(Piece.BISHOP, color=opp_color)
    opp_queens = board.get_piece_bb(Piece.QUEEN, color=opp_color)
    if (get_bishop_moves_bb(my_king_sq, board) & (opp_bishops | opp_queens)) != tables.EMPTY_BB:
        return True

    opp_rooks = board.get_piece_bb(Piece.ROOK, color=opp_color)
    if (get_rook_moves_bb(my_king_sq, board) & (opp_rooks | opp_queens)) != tables.EMPTY_BB:
        return True

    return False
```

And we're done for real this time!

### Evaluation

The third major component of a chess engine is evaluation. The evaluation function takes an arbitrary board state and assigns to it a numeric score: the higher the score, the better off the player to move is. This will be used by the search algorithm to guide our engine in the right direction.

The way evaluation typically works is by combining various *heuristics* that are known to indicate a strong position. This is another area where the bitboard approach shines, since we can express many of these heuristics as simple bitwise operations. For instance, suppose we wanted to know how many of our pieces are in the center of the board? As every beginner chess player knows, this is likely something we're interested in, as a strong center is often the key to a good position. Thankfully, bitboards make this easy:

```python
def eval_center(board):
    """
    Evaluates number of our pieces in center of board
    """
    return Score.CENTER.value * bitboard.pop_count(board.combined_color[board.color] & tables.CENTER)
```

There are a ton of heuristics to consider, and sophisticated chess engines like Stockfish and Komodo use a variety of them to arrive at an (almost always) optimal move. We'll keep things simple, though, and stick to some basic ones:

```python
class Score(Enum):
    PAWN = np.int32(100)
    KNIGHT = np.int32(300)
    BISHOP = np.int32(300)
    ROOK = np.int32(500)
    QUEEN = np.int32(900)
    CHECKMATE = np.int32(-1000000)
    CENTER = np.int32(5)
    MOVE = np.int32(5)

def evaluate(board):
    return eval_pieces(board) + eval_center(board) + eval_moves(board)

def piece_diff(board, piece):
    return np.int32(bitboard.pop_count(board.pieces[board.color][piece])) - np.int32(bitboard.pop_count(board.pieces[~board.color][piece]))

def eval_pieces(board):
    """
    Evaluates material weight difference in our favor
    """
    return (Score.PAWN.value * piece_diff(board, Piece.PAWN)
        + Score.KNIGHT.value * piece_diff(board, Piece.KNIGHT)
        + Score.BISHOP.value * piece_diff(board, Piece.BISHOP)
        + Score.ROOK.value * piece_diff(board, Piece.ROOK)
        + Score.QUEEN.value * piece_diff(board, Piece.QUEEN))

def eval_moves(board):
    """
    Evaluates number of moves available
    NOTE: this considers stalemate to be as bad as checkmate, for simplicity
    """
    num = len(list(movegen.gen_legal_moves(board)))
    if num == 0:
        return Score.CHECKMATE.value
    else:
        return Score.MOVE.value * np.int32(num)
```


### Search

Search is the final component of a chess engine. Given a board state, we'd like to search the game tree resulting from that state to find the optimal move. To do so, we'll use a variant of the *minimax* algorithm called *negamax*. The idea of negamax is that we assume our opponent plays optimally. For a given position, we look at every possible move we could make, and choose the one that minimizes the benefit of the resulting position to our opponent. Meanwhile, the opponent is doing the same thing. Since chess is a 2-player, zero-sum game, the benefit of a position to one player is the negative of the benefit of the position to the opposing player. So really all we're doing is maximizing the value of the resulting position to us.

Ideally we would carry out this process until we reached checkmate. Unfortunately, chess has a [branching factor](https://en.wikipedia.org/wiki/Branching_factor) of ~35, which means that the game tree grows exponentially very quickly. To resolve this issue, we call negamax with a fixed depth - once the depth has been reached, negamax returns the result of the evaluation function on the position, and doesn't recurse any further. Here's the algorithm:

```python
def negamax(board, depth):
    if depth == 0:
        return evaluation.evaluate(board)
    max_score = evaluation.Score.CHECKMATE.value
    for move in movegen.gen_legal_moves(board):
        new_board = board.apply_move(move)
        score = -negamax(new_board, depth-1)
        max_score = max(score, max_score)
    return max_score
```

Negamax gives us the value of the position to the current player. So in order to get the best move, we proceed as follows:

```python
def best_move(board, depth):
    max_score = evaluation.Score.CHECKMATE.value
    for move in movegen.gen_legal_moves(board):
        new_board = board.apply_move(move)
        score = -negamax(new_board, depth-1)
        if score > max_score:
            max_score = score
            best_move = move
    return best_move
```

And that's it! We finally have enough to assemble a working chess engine. 


## Tests

Thoroughly testing a chess program is a challenge in and of itself. One strategy that's often used is called [perft](https://chessprogramming.wikispaces.com/Perft). This is a debugging function that walks the game tree up to some specified depth, and counts the number of leaf nodes (i.e. the number of possible board states at the given depth). We can run perft from a variety of starting positions, and compare our results to known values:

```python
def perft(board, depth):
    if depth == 0:
        return 1
    count = 0
    moves = movegen.gen_legal_moves(board)
    for m in moves:
        count += perft(board.apply_move(m), depth-1)
    return count

def test_new():
    b = ChessBoard()
    b.init_game()
    assert perft(b, 0) == 1
    assert perft(b, 1) == 20
    assert perft(b, 2) == 400
    assert perft(b, 3) == 8902
    assert perft(b, 4) == 197281
```

If our values match the known values, it's a strong signal that our move generation code is correct. Moreover if our values don't match, then we definitely know there's an issue.


I used [pytest](https://docs.pytest.org/en/latest/) for my testing framework. It's a pretty nice python testing tool that eliminates a lot of the boilerplate associated with unittest or other strategies. I have some tests in basic.py just for verifying the basic functionality of my bitboard code, and a couple tests in perft.py for the move generation code. (Unfortunately most perft tests will fail until I implement castling / en-passant).


## Further improvements

My engine is rather primitive at the moment, and could be optimized in a variety of ways. Some potential improvements:

* Alpha-beta pruning - This technique improves on the search algorithm by pruning moves that are guaranteed not to affect the negamax score. This is actually something chess players do without realizing it. The thinking is approximately: "If I make this move m1, all the continuations lead to a good position for me. What if I make move m2? Ah if I do that, then he has a move that leads to a really bad position for me. So I don't even need to consider his other responses to m2."

* Move ordering - Currently the engine generates moves without much thought as to their order. This doesn't matter at the moment since the search algorithm has to consider each move sequence anyway. However, with alpha-beta pruning in place, the move ordering becomes important since we'd like to prune suboptimal branches as early as possible. If we generate the best moves first, then the alpha-beta search will be able to eliminate most of the bad moves right away. An optimal ordering actually lets us calculate to twice the depth in the same amount of time.

* Zobrist hashing - This is a method for implementing transposition tables. In chess, it's often the case that different sequences of moves lead to the same board state ("1. e4 e5 2. Nf3 Nf6" results in the same position as "1. Nf3 Nf6 2. e4 e5", for example). Unfortunately, the negamax algorithm doesn't realize this, since these move sequences lead to different positions in the game tree. Zobrist hashing allows us to memoize negamax results and avoid duplicate computations for transpositions. 

* Quiescence search - One of the problems our engine currently suffers from is called the horizon effect. This arises when negamax reaches its maximum depth and has to return the evaluation of a board position that's still unclear. For instance, in the example game pictured at the beginning of this README, the engine ends up losing its queen after my discovered check. What happened here was that the search depth was 3, and the engine saw that it could keep the queen for 3 turns; however, it failed to realize that it would lose the queen on the 4th turn. Essentially, the horizon it could see was too short. Quiescence search resolves this dilemma by continuing to a search for a "quiet" position if the board is still unclear at the max depth. 

Perhaps in the future I'll implement some of these.

## Resources

There's a lot of information about chess engine programming on the internet, but it's not always very approachable. Code is often presented with a ton of optimizations already in place which makes it difficult to understand conceptually. Also, there's a huge variety of different approaches and designs to choose from, which can be paralyzing when starting out. Here are a couple resources that I personally found useful for writing my engine:

* [https://chessprogramming.wikispaces.com/](https://chessprogramming.wikispaces.com/) - This is the definitive resource for chess engine programming. It's a bit hard to navigate and can be overly technical for a beginner, but all the information you'll ever need is contained in here somewhere.
* [https://github.com/official-stockfish/Stockfish](https://github.com/official-stockfish/Stockfish) - Popular, open source, highly optimized chess engine. 
* [http://pages.cs.wisc.edu/~psilord/blog/data/chess-pages/](http://pages.cs.wisc.edu/~psilord/blog/data/chess-pages/) - Primer on bitboards. Some of the pages are unfinished but nonetheless a good introduction.
* [https://jordanbray.github.io/chess/chess/index.html](https://jordanbray.github.io/chess/chess/index.html) - Move generation library in Rust. Clean code and well-documented. I took inspiration from here for my high-level movegen design.
* [http://www.michaelburge.us/2017/09/10/injecting-shellcode-to-speed-up-amazon-redshift.html](http://www.michaelburge.us/2017/09/10/injecting-shellcode-to-speed-up-amazon-redshift.html) - Small, self-contained chess engine written in C, with a nice walkthrough. I referred to this for some of the evaluation functions.
