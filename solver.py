from group import Group

from board import UNOPENED, FLAG, BOMB
import board
import keyboard
import time


INITIAL_MINES = 99

class Solver():
    def __init__(self):
        # list of Group objects
        self.groups = []
        self.no_more_subgroups = []
        self.at_least_subgroups = []

    def gen_groups(self):
        self.groups = []
        # generate groups
        for i in range(board.width):
            for j in range(board.height):
                if board.board[j][i] > 0 and board.board[j][i] < 9:
                    g = Group()
                    if g.add_group_from_coords(i, j):
                        self.groups.append(g)
                    
    def simple_solve(self):
        '''
        Simple check if there are any groups that have no mines/
        have all mines.
        '''
        changed = False
        for g in self.groups:
            if g.mines == 0:
                for coord in g.coords:
                    board.inter.click(coord[0], coord[1])
                    changed = True
            elif g.mines == len(g.coords):
                for coord in g.coords:
                    board.inter.flag(coord[0], coord[1])
                    changed = True
        return changed

    def group_solve(self):
        '''
        Check groups together to deduce safe tiles and mines.
        '''
        changed = False
        for i in range(len(self.groups)):
            for j in range(i + 1, len(self.groups)):
                changed = self.groups[i].check_safe(self.groups[j]) or changed
                # Check other way for subset
                changed = self.groups[j].check_safe(self.groups[i]) or changed

                changed = self.groups[i].check_mines(self.groups[j]) or changed
                # Check other way for subset
                changed = self.groups[j].check_mines(self.groups[i]) or changed
        return changed
    
    def get_subgroups(self):
        '''
        Saves a list of subgroups that have at least x mines.
        '''
        for g in self.groups:
            if len(g.coords) > 2 or g.mines > 0 or len(g.coords) < 7:
                # add to no more than x mines subgroup
                for coord in g.coords:
                    gg = Group(g.coords - {coord}, g.mines)
                    self.no_more_subgroups.append(gg)
                if g.mines > 1:
                    # add to at least x mines subgroup
                    for coord in g.coords:
                        gg = Group(g.coords - {coord}, g.mines - 1)
                        self.at_least_subgroups.append(gg)

    def subgroup_solve(self):
        '''
        Check subgroups with groups to deduce safe tiles and mines.
        '''
        self.get_subgroups()
        changed = False
        for i in range(len(self.no_more_subgroups)):
            for j in range(len(self.groups)):
                changed = self.no_more_subgroups[i].check_mines(self.groups[j]) or changed
                
        for i in range(len(self.at_least_subgroups)):
            for j in range(len(self.groups)):
                changed = self.at_least_subgroups[i].check_safe(self.groups[j]) or changed
        return changed
    
    def csr_solve(self):
        '''
        Check subgroups together to deduce safe tiles and mines.
        '''
        pass

    def solve(self):
        # first click
        board.inter.click(0, 0)
        # print(self.simple_solve())
        # self.gen_groups()

        # main loop
        while not board.is_done:
            print(board.unopened_tiles)
            # (re)generate groups
            time.sleep(0.5)   
            # print(board.remaining_mines)
            self.gen_groups()
            # print([str(x) for x in self.groups])

            if keyboard.is_pressed('b'):
                break

            if self.simple_solve():
                continue
            if self.group_solve():
                print('group solve')
                continue
            if self.subgroup_solve():
                print('subgroup solve')
                continue

            
