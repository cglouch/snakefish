import numpy as np

import movegen
import evaluation

def negamax(board, depth):
    if depth == 0:
        return evaluation.evaluate(board)
    max_score = evaluation.Score.CHECKMATE.value
    for move in movegen.gen_legal_moves(board):
        new_board = board.apply_move(move)
        score = -negamax(new_board, depth-1)
        max_score = max(score, max_score)
    return max_score

def best_move(board, depth):
    max_score = evaluation.Score.CHECKMATE.value
    for move in movegen.gen_legal_moves(board):
        new_board = board.apply_move(move)
        score = -negamax(new_board, depth-1)
        if score > max_score:
            max_score = score
            best_move = move
    return best_move


