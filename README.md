# Snakefish
A chess engine created from scratch in Python

## Overview
Snakefish uses a bitboard approach to represent the state of the chess board and to generate possible moves. Search is performed using the negamax algorithm with a simple heuristic. 

Check out a sample game I played against Snakefish here! 


## Chess engine basics

There are three main components to a chess engine:

- Board representation
- Evaluation
- Search

We will give an overview of these components and describe how they're implemented in Snakefish.

### Board representation

The first decision one must make when writing a chess engine is deciding on a board representation.  Because engines need to compute a huge number of positions, we want to choose a board representation that allows for efficient move generation and fast evaluation. Unsurprisingly, this turns out to be difficult! Generating moves correctly and efficiently is probably the hardest part of any engine.

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

The advantage of a square-centric representation is that it feels natural. It's pretty easy to mentally translate between a board and its representation, and it lends itself to writing move generation code in a fairly obvious manner: simply iterate through the squares, and for each non-empty square get the moves that can be made with the piece on that square. However, the downside of a square-centric representation is that it tends to be slow. We don't really want to iterate through all 64 squares every time we calculate a move, especially considering that the majority of the squares will be empty! We could alleviate this somewhat by maintaining a list of the non-empty squares, and in practice most square-centric engines do something like this. However, we still end up spending a lot of time iterating.

The second approach to board representation is **piece-centric**. Instead of describing the contents of the squares, we describe the locations of the pieces. There's a variety of ways to do this, but the most ingenious (and thankfully also the most efficient!) is to use **bitboards**. 


### Evaluation



### Search

Chess has a [branching factor](https://en.wikipedia.org/wiki/Branching_factor) of ~35

## Tests




## Resources

chessprogrammingwiki  
stockfish  
rust move gen lib  
chess engine in c amazon redshift
