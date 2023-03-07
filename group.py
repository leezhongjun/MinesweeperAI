from board import UNOPENED, FLAG, BOMB
import board

class Group():
    def __init__(self, coords=set(), mines=0):
        '''
        A group is a set of unopened cells that are adjacent to a cell 
        with the number of mines that they share.
        '''
        # set of coords(x, y)
        self.coords = coords
        self.mines = mines

    def __str__(self) -> str:
        return f"Group: {self.coords}, {self.mines}"

    def add_group_from_coords(self, x, y):
        self.coords = set()
        added = False
        self.mines = board.board[y][x]
        for i in range(-1, 2):
            for j in range(-1, 2):
                if x + i >= 0 and x + i < board.width and \
                    y + j >= 0 and y + j < board.height:
                    if board.board[y + j][x + i] > 8:
                        if board.board[y + j][x + i] == FLAG:
                            self.mines -= 1
                        elif board.board[y + j][x + i] == UNOPENED:
                            self.coords.add((x + i, y + j))
                            added = True
        return added
    
    def check_safe(self, other):
        '''
        Clicks safe coords if other is subset of self
        and mines are equal.
        '''
        if self.mines == other.mines:
            if self.coords.issubset(other.coords):
                subset = other.coords - self.coords
                if len(subset) > 0:
                    for coord in subset:
                        board.inter.click(coord[0], coord[1])
                    return True
        return False
    
    def check_mines(self, other):
        '''
        Flags mine coords if other is subset of self
        and mines are equal.
        '''
        if self.mines < other.mines:
            if self.coords.issubset(other.coords):
                subset = other.coords - self.coords
                if len(subset) == other.mines - self.mines:
                    for coord in subset:
                        board.inter.flag(coord[0], coord[1])
                    return True
        return False
                            