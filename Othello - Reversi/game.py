import yaml

from measure import profile_n, time_n  # Time measurement and Function Calls/Time Profiling

from bitwise_func import set_state, cell_count, print_board, print_pieces
from next import generate_moves, make_move

from minmax_params import Strategy  # Enums for the strategies
from strategies import strategy


def othello(mode: tuple, size: int = 8, max_depth: int = 4, display: bool = False, verbose: bool = False) \
        -> tuple[int, int, int, list]:
    """
    Handles the game logic of Othello. We keep track of the board, the turn, the possible moves and the adjacent
    cells.
    - The game is played on a 8x8 board by default.
    - The game is played by two players, one with the black pieces (value -1) and one with the white pieces (value +1).
    Empty cells are represented by 0.
    - The game starts with 2 black pieces and 2 white pieces in the center of the board.

    The play mode is defined as follows:
    0 for Human, >=1 for Bot (1: random, 2: positional with TABLE1, 3: positional with TABLE2, 4: absolute, 5: mobility,
    6: mixed with TABLE1, 7: mixed with TABLE2)

    Args:
        mode (tuple): describe the strategy and the player type. Index 0 is Black, and 1 is White.
        size (int, optional): size of the board. Defaults to 8.
        max_depth (int, optional): max depth of the search tree. Defaults to 4.
        display (bool, optional): display the board for the bots. Defaults to False.
        verbose (bool, optional): print the winner. Defaults to False.

    Returns:
        int: return code. -1 if black wins, 0 if tied, 1 if white wins
    """
    error_handling(mode, size)
    white_pieces, black_pieces = init_bit_board(size)  # set the bit board
    turn = -1  # Black starts

    while True:
        if verbose == 2:
            print("Turn: " + ("Black" if turn == -1 else "White"))
            print_board(white_pieces, black_pieces, size)
            print_pieces(white_pieces, size)
            print_pieces(black_pieces, size)

        own, enemy = (black_pieces, white_pieces) if turn == -1 else (white_pieces, black_pieces)
        moves, directions = generate_moves(own, enemy, size)

        if not moves:  # verify if the other player can play
            if len(generate_moves(enemy, own, size)[0]) == 0:
                break  # end the game loop
            turn *= -1
            continue  # skip the current turn

        next_move = strategy(mode, white_pieces, black_pieces, moves, turn, display, size, max_depth)
        black_pieces, white_pieces = make_move(own, enemy, next_move, directions, size)
        # swap the players after the move
        if turn == 1:
            white_pieces, black_pieces = black_pieces, white_pieces
        turn *= -1
    return get_winner(white_pieces, black_pieces, verbose), white_pieces, black_pieces, moves


def error_handling(mode: tuple, size: int) -> int:
    """
    Check if the input parameters are correct

    Args:
        mode (tuple): describe the strategy and the player type.
        size (int): size of the board
    """
    if size < 4:
        raise ValueError("Size must be at least 4")
    if size % 2 != 0:
        raise ValueError("Size must be an even number")
    if not all(Strategy.HUMAN <= m <= Strategy.MIXED_TABLE2 for m in mode):
        raise NotImplementedError("Invalid mode")
    if size != 8 and any(mode) in [Strategy.POSITIONAL_TABLE1, Strategy.POSITIONAL_TABLE2, Strategy.MIXED_TABLE1,
                                   Strategy.MIXED_TABLE2]:
        raise ValueError("Size must be 8 to use heuristic tables (TABLE1, TABLE2 are used by {2, 3, 6, 7})")
    return 0


def init_bit_board(size) -> tuple[int, int]:
    """Set the starting positions for the white and black pieces"""
    white_pieces = set_state(0, size // 2 - 1, size // 2 - 1, size)
    white_pieces = set_state(white_pieces, size // 2, size // 2, size)
    black_pieces = set_state(0, size // 2 - 1, size // 2, size)
    black_pieces = set_state(black_pieces, size // 2, size // 2 - 1, size)
    return white_pieces, black_pieces


def get_winner(white_pieces: int, black_pieces: int, verbose: bool) -> int:
    """Print the winner and return the code of the winner

    Args:
        white_pieces (int): a bit board of the current player
        black_pieces (int): a bit board of the other player
        verbose (bool): print or not the winner
    
    Returns:
        int: return code. -1 if black wins, 0 if tied, 1 if white wins
    """
    black = cell_count(black_pieces)
    white = cell_count(white_pieces)
    if black > white:
        if verbose:
            print("Black wins" + "(" + str(black) + " vs " + str(white) + ")")
        return -1
    if black < white:
        if verbose:
            print("White wins" + "(" + str(white) + " vs " + str(black) + ")")
        return 1
    if verbose:
        print("Draw" + "(" + str(black) + " vs " + str(white) + ")")
    return 0


def main():
    with open("F:/Workspaces/PyCharm/IA - Fondements/Othello - Reversi/config.yaml", "r") as file:
        config = yaml.safe_load(file)
    mode = (int(config["mode"][0]), int(config["mode"][1]))
    size = int(config["size"])
    max_depth = int(config["max_depth"])
    display = config["display"]
    verbose = config["verbose"]

    time_n(othello, config["n"], (mode, size, max_depth, display, verbose))
    profile_n(othello, config["n"], (mode, size, max_depth, display, verbose))


if __name__ == "__main__":
    main()
