from next import generate_moves, make_move
# from bitwise_func import print_board


class Node:
    def __init__(self, parent, own_pieces, enemy_pieces, turn, size):
        self.parent = parent
        self.own_pieces = own_pieces
        self.enemy_pieces = enemy_pieces
        self.turn = turn
        self.size = size
        self.children = []
        self.moves = []
        self.directions = {}
        self.value = None
        self.best_move = None
        self.visited = False

    def expand(self):
        self.moves, self.directions = generate_moves(self.own_pieces, self.enemy_pieces, self.size)
        # for move in self.moves:
        #     own, enemy = make_move(self.own_pieces, self.enemy_pieces, move, self.directions)
        #     self.children.append(Node(self, enemy, own, -self.turn, self.size))
        self.children = [Node(self, *make_move(self.own_pieces, self.enemy_pieces, move, self.directions)[::-1],
                              -self.turn, self.size)
                         for move in self.moves]
        self.visited = True

    def get_other_child(self, other):
        for i, child in enumerate(self.children):
            if child == other:
                # print("got it")
                return child
            else:
                pass
                # print(f"child {i}:")
                # print_board(child.own_pieces, child.enemy_pieces, size=self.size)
        # print("caca")
        return None

    def __eq__(self, other):
        return self.own_pieces == other.own_pieces and self.enemy_pieces == other.enemy_pieces

    def __hash__(self):
        return hash((self.own_pieces, self.enemy_pieces, self.turn))

    def __repr__(self):
        return f"{self.own_pieces}, {self.enemy_pieces}, {self.turn}"

    def __str__(self):
        return f"{self.own_pieces}, {self.enemy_pieces}, {self.turn}"
