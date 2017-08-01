from chessboard import ChessBoard
from move import Move
from square import Square
from constants import Piece
import search


def get_move():
    src = input("From: ")
    dest = input("To: ")
    promo = input("Promo: ").lower()
    promo_piece = next(
            (p for p in Piece if p.to_char() == promo),
            None)
    return Move(Square.from_str(src), Square.from_str(dest), promo_piece)

def main():
    # NOTE: currently doesn't validate move or stop at checkmate, just plays
    # This is really just for generating example game gif
    board = ChessBoard()
    board.init_game()
    print("Initial board")
    print("\n")
    print(board)
    print("\n")

    while True:
        print("Enter your move")
        print("\n")
        player_move = get_move()
        board = board.apply_move(player_move)
        print("\n")
        print("Board is now:")
        print(board)
        print("\n")

        engine_move = search.best_move(board, 3)
        print(engine_move)
        board = board.apply_move(engine_move)
        print("\n")
        print("Board is now:")
        print(board)
        print("\n")


if __name__ == "__main__":
    main()
