import numpy as np
import random

from visualize import cv2_display
from minmax_params import TABLE1, TABLE2, MAX_DEPTH, MAX_INT

from tqdm import tqdm
import time
import cProfile
import pstats

from typing import Tuple

DIRECTIONS = {(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)}


def othello(mode: tuple, size: int = 8, display: bool = False, verbose: bool = False) \
        -> Tuple[int, np.ndarray, list, set]:
    """
    Handles the game logic of Othello. We keep track of the board, the turn, the possible moves and the adjacent
    cells. - The game is played on a 8x8 board by default. - The game is played by two players, one with the black
    pieces (value -1) and one with the white pieces (value +1). Empty cells are represented by 0. - The game starts
    with 2 black pieces and 2 white pieces in the center of the board.

    Args: mode (tuple): describe the strategy and the player type. 0: Human, >=1: Bot (1: random, 2: positional with
    TABLE1, 3: positional with TABLE2, 4: absolute, 5: mobility, 6: mixed) size (int, optional): size of the board.
    Defaults to 8. display (bool, optional): display the board for the bots. Defaults to False. verbose (bool,
    optional): print the winner. Defaults to False. Returns: int: return code. -1 if black wins, 0 if drawn,
    1 if white wins
    """
    error_handling(mode, size)
    board = np.zeros((size, size), dtype=np.int8)
    adjacent_cells = set()
    turn = -1  # Black starts
    init_board(board)  # set the starting positions
    init_adjacent_cells(adjacent_cells)  # set the adjacent cells
    moves = []

    while len(adjacent_cells) >= 0:
        moves, invalid_directions = get_possible_moves(board, adjacent_cells, turn, size)  # set the possible moves

        if len(moves) == 0:
            # verify if the other player can play
            if len(get_possible_moves(board, adjacent_cells, -turn, size)[0]) == 0:
                break
            turn *= -1
            continue

        next_move = strategy(mode, board, moves, turn, adjacent_cells.copy(), display, size)
        play(board, next_move, turn, adjacent_cells, invalid_directions,
             size)  # flip the cells, update adjacent cells, update possible moves
        turn *= -1

    return get_winner(board, verbose), board, moves, adjacent_cells


def error_handling(mode: tuple, size: int) -> int:
    """
    Check if the input parameters are correct

    Args: mode (tuple): describe the strategy and the player type. 0: Human, >=1: Bot (1: random, 2: postional,
    3: absolute, 4: mobility, 5: mixed). For example: (0, 1) means Human vs Bot with the random strategy size (int):
    size of the board
    """
    if size < 4:
        raise ValueError("Size must be at least 4")
    if size % 2 != 0:
        raise ValueError("Size must be an even number")
    if not all(0 <= m <= 5 for m in mode):
        raise ValueError("Invalid mode")
    return 0


def init_board(board: np.ndarray, size: int = 8) -> None:
    """
    Set the starting positions of the board

    Args:
        board (np.ndarray): board state
        size (int, optional): size of the board. Defaults to 8.
    """
    board[size // 2 - 1][size // 2 - 1] = 1
    board[size // 2][size // 2] = 1
    board[size // 2 - 1][size // 2] = -1
    board[size // 2][size // 2 - 1] = -1


def init_adjacent_cells(adjacent_cells: set, size: int = 8) -> None:
    """
    Set the adjacent cells

    Args:
        adjacent_cells (set): set of adjacent cells
        size (int, optional): size of the board. Defaults to 8.
    """
    adjacent_cells.update(
        [(size // 2 - 2, size // 2 - 1), (size // 2 - 1, size // 2 - 2), (size // 2 - 2, size // 2 - 2),  # top left
         (size // 2 + 1, size // 2), (size // 2, size // 2 + 1), (size // 2 + 1, size // 2 + 1),  # bottom right
         (size // 2 - 2, size // 2), (size // 2 - 2, size // 2 + 1), (size // 2 - 1, size // 2 + 1),  # bottom left
         (size // 2 + 1, size // 2 - 1), (size // 2, size // 2 - 2), (size // 2 + 1, size // 2 - 2)])  # top right


def get_possible_moves(board: np.ndarray, adjacent_cells: set, turn: int, size: int) -> Tuple[list, set]:
    """
    Get the possible moves of the current player

    Args:
        board (np.ndarray): board state
        adjacent_cells (set): set of adjacent cells
        turn (int): current player
        size (int): size of the board

    Returns:
        list: list of possible moves
        set: set of invalid directions
    """
    possible_moves = []
    invalid_directions = set()
    for x, y in adjacent_cells:
        for dx, dy in DIRECTIONS:
            is_valid, n_jump = is_valid_direction(board, x, y, dx, dy, turn, size)
            if is_valid:
                possible_moves.append((x, y, n_jump, dx, dy))
                break
            else:
                invalid_directions.add((dx, dy))
        invalid_directions = set()
    return possible_moves, invalid_directions


def is_valid_direction(board: np.ndarray, x: int, y: int, dx: int, dy: int, turn: int, size: int) -> Tuple[bool, int]:
    """Check if the direction is valid, also return the last cell of the direction

    Args:
        board (np.ndarray): board state
        x (int): x coordinate
        y (int): y coordinate
        dx (int): x direction
        dy (int): y direction
        turn (int): current player
        size (int): size of the board

    Returns:
        bool: True if the direction is valid
        int: number of jumps
    """
    x += dx
    y += dy
    n_jump = 0
    for _ in range(size):
        if x < 0 or x >= size or y < 0 or y >= size or board[x][y] != -turn:
            break
        x += dx
        y += dy
        n_jump += 1
    return 0 <= x < size and 0 <= y < size and board[x][y] == turn and n_jump > 0, n_jump


def play(board: np.ndarray, move: tuple, turn: int, adjacent_cells: set, invalid_directions: set, size: int) -> None:
    """Play the move

    Args:
        board (np.ndarray): board state
        move (tuple): next move
        turn (int): current player
        adjacent_cells (set): set of adjacent cells
        invalid_directions (set): set of invalid directions
        size (int): size of the board
    """
    x, y, n_jump, dx, dy = move
    old_x, old_y = x, y
    board[x][y] = turn
    # We update the direction we know for sure is valid
    for _ in range(n_jump):
        x += dx
        y += dy
        board[x][y] = turn
    x, y = old_x, old_y
    # We update other possible directions (the break in the get_possible_moves function prevent us from having more
    for dx, dy in DIRECTIONS - invalid_directions - {(dx, dy)}:
        is_valid, n_jump = is_valid_direction(board, x, y, dx, dy, turn, size)
        if is_valid:
            for _ in range(n_jump):
                x += dx
                y += dy
                board[x][y] = turn
            x, y = old_x, old_y

    # update adjacent cells
    adjacent_cells.discard((old_x, old_y))
    for dx, dy in DIRECTIONS:
        if 0 <= old_x + dx < size and 0 <= old_y + dy < size:
            if board[old_x + dx][old_y + dy] == 0:
                adjacent_cells.add((old_x + dx, old_y + dy))


def strategy(mode: tuple, board: np.ndarray, moves: list, turn: int, adjacent_cells: set, display: bool,
             size: int) -> tuple:
    """Return the next move

    Args: mode (tuple): describe the strategy and the player type. 0: Human, >=1: Bot (1: random, 2: postional with
    TABLE1, 3: postional with TABLE2, 4: absolute, 5: mobility, 6: mixed) board (np.ndarray): board state moves (
    list): list of possible moves turn (int): current player adjacent_cells (set): set of adjacent cells display (
    bool): display the board for the bots size (int): size of the board

    Returns:
        tuple: next move
    """
    if display:
        cv2_display(size, board, moves, turn, adjacent_cells, display_only=True)

    if turn == -1:
        player = mode[0]
    else:
        player = mode[1]

    if player == 0:
        return s_human(board, moves, adjacent_cells, turn, size)
    if player == 1:
        return s_random(moves)
    if player == 2:
        return s_positional(board, adjacent_cells, turn, 0, TABLE1, size, -MAX_INT, MAX_INT)[1]
    if player == 3:
        return s_positional(board, adjacent_cells, turn, 0, TABLE2, size, -MAX_INT, MAX_INT)[1]
    if player == 4:
        return s_absolute(board, adjacent_cells, turn, 0, size, -MAX_INT, MAX_INT)[1]
    if player == 5:
        return s_mobility(board, adjacent_cells, turn, 0, size, -MAX_INT, MAX_INT)[1]
    if player == 6:
        return s_mixed(board, adjacent_cells, turn, 0, TABLE1, size, -MAX_INT, MAX_INT)[1]
    if player == 7:
        return s_mixed(board, adjacent_cells, turn, 0, TABLE2, size, -MAX_INT, MAX_INT)[1]


def s_random(moves: list) -> tuple:
    """Return a random move

    Args:
        moves (list): list of possible moves

    Returns:
        tuple: next move
    """
    return random.choice(moves)


def s_human(board: np.ndarray, moves: list, adj_cells, turn, size: int) -> tuple:
    """Display the board using cv2 and return a move from the user
    
    Args:
        board (np.ndarray): board state
        moves (list): list of possible moves
        adj_cells (set): set of adjacent cells
        turn (int): current player
        size (int): size of the board
        
    Returns:
        tuple: next move
    """
    return cv2_display(size, board, moves, turn, adj_cells)


def s_absolute(board: np.ndarray, adjacent_cells: set, turn: int, depth: int, size: int, alpha: int,
               beta: int) -> tuple | list:
    """
    Looks at the number of pieces flipped (tries to maximize (player's pieces - opponent's pieces)). MinMax (NegaMax)
    algorithm with alpha-beta pruning.
    
    Args:
        board (np.ndarray): board state
        adjacent_cells (set): set of adjacent cells
        turn (int): current player
        depth (int): depth of the search
        size (int): size of the board
        alpha (int): alpha value
        beta (int): beta value
        
    Returns:
        tuple: best score, best move        
    """
    if depth == MAX_DEPTH or len(adjacent_cells) == 0:
        return [np.sum(board == turn) - np.sum(board == -turn)]
    moves, invalid_directions = get_possible_moves(board, adjacent_cells, turn, size)
    if len(moves) == 0:
        return [np.sum(board == turn) - np.sum(board == -turn)]

    best = -MAX_INT
    best_moves = []
    for move in moves:
        board_copy = board.copy()
        adj_cells = adjacent_cells.copy()
        play(board_copy, move, turn, adj_cells, invalid_directions, size)
        score = -s_absolute(board_copy, adj_cells, -turn, depth + 1, size, -beta, -alpha)[0]
        if score == best:
            best_moves.append(move)
        if score > best:
            best = score
            best_moves = [move]
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    best_move = random.choice(best_moves)
    return best, best_move


def s_positional(board: np.ndarray, adjacent_cells: set, turn: int, depth: int, table: np.ndarray, size: int,
                 alpha: int, beta: int) -> tuple | list:
    """Return the best move using heuristics. MinMax (NegaMax) algorithm with alpha-beta pruning
    
    Args:
        board (np.ndarray): board state
        adjacent_cells (set): set of adjacent cells
        turn (int): current player
        depth (int): depth of the search
        table (np.ndarray): table of adjacent cells
        size (int): size of the board
        alpha (int): alpha value
        beta (int): beta value
        
    Returns:
        tuple: best score, best move
    """
    if depth == MAX_DEPTH or len(adjacent_cells) == 0:
        return [np.sum(table[np.where(board == turn)]) - np.sum(table[np.where(board == -turn)])]
    moves, invalid_directions = get_possible_moves(board, adjacent_cells, turn, size)
    if len(moves) == 0:
        return [np.sum(table[np.where(board == turn)]) - np.sum(table[np.where(board == -turn)])]
    best = -MAX_INT
    best_moves = []
    for move in moves:
        board_copy = board.copy()
        adj_cells = adjacent_cells.copy()
        play(board_copy, move, turn, adj_cells, invalid_directions, size)
        score = -s_positional(board_copy, adj_cells, -turn, depth + 1, table, size, -beta, -alpha)[0]
        if score == best:
            best_moves.append(move)
        if score > best:
            best = score
            best_moves = [move]
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    best_move = random.choice(best_moves)
    return best, best_move


def s_mobility(board: np.ndarray, adjacent_cells: set, turn: int, depth: int, size: int, alpha: int,
               beta: int) -> tuple | list:
    """Return the best move using the mobility. Maximize the number of possible moves for the current player,
    and minimize the number of possible moves for the other player. MinMax (NegaMax) algorithm with alpha-beta pruning
    
    Args:
        board (np.ndarray): board state
        adjacent_cells (set): set of adjacent cells
        turn (int): current player
        depth (int): depth of the search
        size (int): size of the board
        alpha (int): alpha value
        beta (int): beta value
        
    Returns:
        int: best score, best move
    """
    if len(adjacent_cells) == 0:
        return [turn]
    moves, invalid_directions = get_possible_moves(board, adjacent_cells, turn, size)
    length_moves = len(moves)
    if depth == MAX_DEPTH or size == 0:
        return [length_moves - len(get_possible_moves(board, adjacent_cells, -turn, size)[0])]

    best = -MAX_INT
    best_moves = []
    for move in moves:
        board_copy = board.copy()
        adj_cells = adjacent_cells.copy()
        play(board_copy, move, turn, adj_cells, invalid_directions, size)
        score = -s_mobility(board_copy, adj_cells, -turn, depth + 1, size, -beta, -alpha)[0]
        if score == best:
            best_moves.append(move)
        if score > best:
            best = score
            best_moves = [move]
            if best > alpha:
                alpha = best
                if alpha >= beta:
                    break
    best_move = random.choice(best_moves)
    return best, best_move


def s_mixed(board: np.ndarray, adjacent_cells: set, turn: int, depth: int, table: np.ndarray, size: int, alpha: int,
            beta: int) -> tuple:
    """Return the best move using phases. First phase (0-20) we use positional, then mobility, then absolute (
    44-64). The idea is we get a positional advantage early, then we try to make it hard for the opponent to play,
    then we maximize the number of pieces flipped

    Args:
        board (np.ndarray): board state
        adjacent_cells (set): set of adjacent cells
        turn (int): current player
        depth (int): depth of the search
        table (np.ndarray): table of values
        size (int): size of the board
        alpha (int): alpha value
        beta (int): beta value
        
    Returns:
        int: best score, best move
    """
    if np.sum(board != 0) < 20:
        return s_positional(board, adjacent_cells, turn, depth, table, size, alpha, beta)
    if np.sum(board != 0) < 50:
        return s_mobility(board, adjacent_cells, turn, depth, size, alpha, beta)
    return s_absolute(board, adjacent_cells, turn, depth, size, alpha, beta)


def get_winner(board: np.ndarray, verbose: bool) -> int:
    """Print the winner and return the code of the winner

    Args:
        board (np.ndarray): board state
        verbose (bool): print or not the winner
    
    Returns:
        int: return code. -1 if black wins, 0 if drawn, 1 if white wins
    """
    black = np.sum(board == -1)
    white = np.sum(board == 1)
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


def profile(params: tuple) -> Tuple[int, np.ndarray, list, set]:
    """Profile the code

    Args:
        params (tuple): parameters of the game
    """
    prof = cProfile.Profile()
    prof.enable()
    code, board, moves, adj_cells = othello(*params)
    prof.disable()
    stats = pstats.Stats(prof).sort_stats('cumulative')
    stats.print_stats()
    return code, board, moves, adj_cells


def time_n(n: int, params: tuple) -> Tuple[int, np.ndarray, list, set]:
    """Time the code

    Args:
        n (int): number of iterations
        params (tuple): parameters of the game
    """
    onset = time.time()
    wins = []
    code, board, moves, adj_cells = -1, np.zeros((params[1], params[1]), dtype=np.int8), [], set()
    for _ in tqdm(range(n), desc="Progress", unit="iteration"):
        code, board, moves, adj_cells = othello(*params)
        wins.append(code)

    offset = time.time()
    print("\nTime:", offset - onset, "s")
    if n > 1:
        print("Average time:", (offset - onset) / n)
        print("Black won:", wins.count(-1), '(' + str(wins.count(-1) / n * 100) + '%)')
        print("White won:", wins.count(1), '(' + str(wins.count(1) / n * 100) + '%)')
        print("Draw:", wins.count(0), '(' + str(wins.count(0) / n * 100) + '%)')
    return code, board, moves, adj_cells


if __name__ == "__main__":
    # code, board, moves, adj_cells = profile(((1, 1), 8, False, True))
    r_code, r_board, r_moves, r_adj_cells = time_n(10, ((0, 5), 8, True, True))
    # cv2_display(8, board, moves, 1, adj_cells, display_only=True, last_display=True)