import yaml

from bitwise_func import set_state, cell_count, print_board, print_pieces
from measure import profile_n, time_n  # Time measurement and Function Calls/Time Profiling
from minmax_params import Strategy  # Enums for the strategies
from next import get_next_moves, make_move
from strategies import strategy


def othello(minimax_mode: tuple, mode: tuple, size: int = 8, max_depth: int = 4,
            display: bool = False, verbose: bool = False, save_moves: bool = False) -> tuple[int, int, int, int]:
    """
    Handles the game logic of Othello. The game is played on a 8x8 board by default by two players, one with the black
    pieces (value -1) and one with the white pieces (value +1). The game starts with 2 black pieces and 2 white pieces
    in the center of the board.


    Args:
        minimax_mode (tuple): describe the strategy and the player type. First element is Black, and second is White.
        mode (tuple): describe the strategy and the player type. First element is Black, and second is White.
        size (int, optional): size of the board. Defaults to 8.
        max_depth (int, optional): max depth of the search tree. Defaults to 4.
        display (bool, optional): display the board for the bots. Defaults to False.
        verbose (bool, optional): print the winner. Defaults to False.
        save_moves (bool, optional): save the moves as knowledge for each player (separately). Defaults to False.

    Returns:
        tuple[int, int, int]: return code, white pieces, black pieces
    """
    error_handling(minimax_mode, mode, size)
    enemy, own = init_bit_board(size)  # set the bit board
    turn = -1  # Black starts

    count_level = 0
    own_knowledge = {count_level: {}}  # black knowledge initialized
    enemy_knowledge = {count_level: {}}  # white knowledge initialized

    while True:
        if verbose == 2:
            status(own, enemy, size, turn)

        moves, directions = get_next_moves(own, enemy, size, save_moves, own_knowledge, count_level)

        if not moves:  # Verify if the other player can play
            if not get_next_moves(enemy, own, size, save_moves, enemy_knowledge, count_level)[0]:
                break  # End the game loop
            own, enemy = enemy, own  # swap the players
            own_knowledge, enemy_knowledge = enemy_knowledge, own_knowledge  # swap the knowledge
            turn *= -1
            if save_moves:
                if count_level in own_knowledge:
                    del own_knowledge[count_level]
                else:
                    del enemy_knowledge[count_level]
            continue  # Skip the current turn

        next_move = strategy(minimax_mode, mode, own, enemy, moves, turn, display, size, max_depth,
                             save_moves, own_knowledge, count_level)  # Get the next move
        enemy, own = make_move(own, enemy, next_move, directions)  # Play and Swap the players
        own_knowledge, enemy_knowledge = enemy_knowledge, own_knowledge  # swap the knowledge
        turn *= -1

        if save_moves:
            if count_level in own_knowledge:
                del own_knowledge[count_level]
            else:
                del enemy_knowledge[count_level]
        count_level += 1

    white_pieces, black_pieces = (own, enemy) if turn == 1 else (enemy, own)
    return get_winner(white_pieces, black_pieces, verbose), own, enemy, turn


def error_handling(minimax_mode: tuple, mode: tuple, size: int) -> int:
    """
    Check if the input parameters are correct

    Args:
        minimax_mode (tuple): describe the version to use for the minimax algorithm.
        mode (tuple): describe the strategy and the player type.
        size (int): size of the board
    """
    if size < 4:
        raise ValueError("Size must be at least 4")
    if size % 2 != 0:
        raise ValueError("Size must be an even number")

    if not all(Strategy.HUMAN <= m <= Strategy.MIXED_TABLE2 for m in mode):
        raise NotImplementedError("Invalid mode")
    if not all(Strategy.MINIMAX <= m <= Strategy.NEGAMAX_ALPHA_BETA for m in minimax_mode):
        raise NotImplementedError("Invalid minimax mode")

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


def status(own: int, enemy: int, size: int, turn: int) -> None:
    print("Turn: " + ("Black" if turn == -1 else "White"))
    white_pieces, black_pieces = (own, enemy) if turn == 1 else (enemy, own)
    print_board(white_pieces, black_pieces, size)
    print_pieces(white_pieces, size)
    print_pieces(black_pieces, size)
    print(f"{white_pieces:064b}")
    print(f"{black_pieces:064b}")
    print(white_pieces | black_pieces)


def main():
    with open("F:/Workspaces/PyCharm/IA - Fondements/Othello - Reversi/config.yaml", "r") as file:
        config = yaml.safe_load(file)
    minimax_mode = (int(config["minimax_mode"][0]), int(config["minimax_mode"][1]))
    mode = (int(config["mode"][0]), int(config["mode"][1]))
    size = int(config["size"])
    max_depth = int(config["max_depth"])
    display = config["display"]
    verbose = config["verbose"]
    save_moves = config["save_moves"]

    time_n(othello, config["n"], (minimax_mode, mode, size, max_depth, display, verbose, save_moves))
    profile_n(othello, config["n"], (minimax_mode, mode, size, max_depth, display, verbose, save_moves))


if __name__ == "__main__":
    main()
