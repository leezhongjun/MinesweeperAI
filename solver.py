from group import Group
from board import UNOPENED, FLAG, BOMB
import board

import keyboard
import time
import itertools
import math


class Solver():
    def __init__(self):

        # List of Group objects
        self.groups = []
        self.no_more_subgroups = []
        self.at_least_subgroups = []

        # List of Group objects in each coupled group
        self.coupled_groups = []

        # List of dict of {coordinate: index} in each coupled group
        self.coupled_groups_lists = []

        # List of list of all coordinates in each coupled group
        self.coupled_groups_temp = []

        # List of solutions sets (from length 0 to 20)
        self.solution_sets = []


    def gen_groups(self):
        '''
        Generate groups from the board.
        '''

        # Clear groups
        self.groups = []
        
        for i in range(board.width):
            for j in range(board.height):

                # If tile is numbered, add group
                if board.board[j][i] > 0 and board.board[j][i] < 9:
                    g = Group()
                    if g.add_group_from_coords(i, j) and (g not in self.groups):
                        self.groups.append(g)


    def simple_solve(self):
        '''
        Simple check if there are any groups that 
        have no mines/have all mines.
        Returns True if any changes were made.
        '''

        changed = False
        for g in self.groups:

            # No mines
            if g.mines == 0:
                for coord in g.coords:
                    board.inter.click(coord[0], coord[1])
                    changed = True
            
            # All are mines
            elif g.mines == len(g.coords):
                for coord in g.coords:
                    board.inter.flag(coord[0], coord[1])
                    changed = True
            
        return changed


    def group_solve(self):
        '''
        Check groups together to deduce safe tiles and mines.
        Returns True if any changes were made.
        '''

        changed = False
        for i in range(len(self.groups)):
            for j in range(i + 1, len(self.groups)):
                
                # Check if safe
                changed = self.groups[i].check_safe(self.groups[j]) or changed
                # Check other way for subset
                changed = self.groups[j].check_safe(self.groups[i]) or changed

                # Check if mine
                changed = self.groups[i].check_mines(self.groups[j]) or changed
                # Check other way for subset
                changed = self.groups[j].check_mines(self.groups[i]) or changed
        
        return changed
    

    def gen_subgroups(self):
        '''
        Generates subgroups that have at least x mines
        or no more than x mines.
        '''

        for g in self.groups:

            # Only add groups with more than 2 tiles
            # and at least 1 mines 
            # and less than 7 tiles (unlikely to be solved, exclude for faster solving)
            if len(g.coords) > 2 or g.mines > 0 or len(g.coords) < 7:

                # Add to no more than x mines subgroup
                for coord in g.coords:
                    gg = Group(g.coords - {coord}, g.mines)
                    self.no_more_subgroups.append(gg)
                
                # Add to at least x mines subgroup
                if g.mines > 1:
                    for coord in g.coords:
                        gg = Group(g.coords - {coord}, g.mines - 1)
                        self.at_least_subgroups.append(gg)


    def subgroup_solve(self):
        '''
        Check subgroups with groups to deduce safe tiles and mines.
        '''

        # Generate subgroups
        self.gen_subgroups()
        
        # Check subgroups with groups
        changed = False
        for i in range(len(self.no_more_subgroups)):
            for j in range(len(self.groups)):
                changed = self.no_more_subgroups[i].check_mines(self.groups[j]) or changed
                
        for i in range(len(self.at_least_subgroups)):
            for j in range(len(self.groups)):
                changed = self.at_least_subgroups[i].check_safe(self.groups[j]) or changed
        
        return changed
    
    def gen_solution_sets(self):
        '''
        Generate all possible solutions sets of 0 to n length.
        '''

        self.solution_sets = []
        l = [0, 1]
        for i in range(20):
            self.solution_sets.append(list(itertools.product(l, repeat=i)))
        

    def create_coupled_groups(self):
        '''
        Creates a list of subsets of groups 
        that are coupled if they share a common tile.
        '''

        # Clear coupled groups
        self.coupled_groups =[]
        self.coupled_groups_lists = []
        self.coupled_groups_temp = []

        # Create coupled groups
        for i in range(len(self.groups)):
            temp = self.groups[i].coords.copy()
            temp_groups = [self.groups[i]]
            append = False

            for j in range(i + 1, len(self.groups)):
                # If groups share a tile or more (intersection), add to coupled group
                if self.groups[i].coords & self.groups[j].coords:
                    temp_groups.append(self.groups[j])
                    temp |= self.groups[j].coords
                    append = True
            
            # Add to coupled groups
            if append:
                self.coupled_groups.append(temp_groups)
                temp = list(temp)
                self.coupled_groups_lists.append({c: i for i, c in enumerate(temp)})
                self.coupled_groups_temp.append(temp.copy())


    def solve_coupled_group(self, coupled_group, coupled_groups_list):
        '''
        For a coupled group, 
        return all solved solutions,
        and the number of possible combinations of bombs (solution weights).
        '''
        
        # Select solution set based on number of groups in coupled group
        if len(coupled_groups_list) < len(self.solution_sets):
            sols = self.solution_sets[len(coupled_groups_list)]
        else:
            sols = list(itertools.product([0, 1], repeat=len(coupled_groups_list)))
        res = []
        comb_ls =[]

        # For each solution in solution set
        for sol in sols:

            # Test solution
            if self.try_coupled_group(coupled_group, coupled_groups_list, sol):

                # Count mines in solution
                mines = sum(sol)

                # Check if number of mines is valid
                if mines <= board.remaining_mines:
                    res.append(sol)
                    # Get no of possible combinations of bombs 
                    # with remaining mines and tiles after using the solution
                    comb = math.comb(board.unopened_tiles - len(coupled_groups_list), board.remaining_mines - mines)
                    comb_ls.append(comb)

        return res, comb_ls


    def try_coupled_group(self, coupled_group, coupled_group_list, solution):
        '''
        For a coupled group, try to solve it with the solution provided.
        Returns True if the solution is valid.
        '''
        
        # For each group in coupled group
        for g in coupled_group:
            mines = g.mines
            length = len(g.coords)

            # For each tile in group
            for i, coord in enumerate(g.coords):
                if solution[coupled_group_list[coord]] == 1:
                    # Solution says this is a mine
                    if mines > 0:
                        mines -= 1
                    else:
                        return False
                else:
                    # Solution says this is a safe tile
                    # Check if remaining tiles should all be mines
                    if mines >= length - i:
                        return False
                    
        return True
                    

    def solve_coupled_groups(self):
        '''
        Solve all coupled groups.
        '''

        changed = False
        for i in range(len(self.coupled_groups)):
            # For each coupled group, solve it
            solutions, comb_ls = self.solve_coupled_group(self.coupled_groups[i], self.coupled_groups_lists[i])
            
            # Loop through solutions, get probabilities
            prob_d = {}
            if solutions:
                for j in range(len(solutions[0])):
                    mine = 0
                    safe = 0
                    
                    # Sum up number of mines and safe tiles, taking into weight
                    for k, sol in enumerate(solutions):
                        if sol[j] == 1:
                            mine += comb_ls[k]
                        else:
                            safe += comb_ls[k]
                    
                    if safe and mine == 0:
                        board.inter.click(self.coupled_groups_temp[i][j][0], self.coupled_groups_temp[i][j][1])
                        changed = True
                    elif mine and safe == 0:
                        board.inter.flag(self.coupled_groups_temp[i][j][0], self.coupled_groups_temp[i][j][1])
                        changed = True

                    # Calculate probability
                    elif not changed and safe and mine:
                        prob = mine / (mine + safe)
                        if self.coupled_groups_temp[i][j] in prob_d:
                            prob_d[self.coupled_groups_temp[i][j]] = (prob_d[self.coupled_groups_temp[i][j]] + prob) / 2
                        else:
                            prob_d[self.coupled_groups_temp[i][j]] = prob
        
        if changed or len(self.coupled_groups) == 0: 
            return
        
        else:
            # print('Probabilities:', prob_d) # Debug
            # Sort by least probability
            ls = [(k, v) for k, v in sorted(prob_d.items(), key=lambda item: item[1])]
            
            
            if ls:
                # Current least probability
                c_prob = ls[0][1]
                
                # Get probability of mine in unconstrained tile
                uncon_prob = board.remaining_mines / board.unopened_tiles

                # Compare probabilities
                if c_prob < uncon_prob:
                    board.inter.click(ls[0][0][0], ls[0][0][1])

                else:
                    # Get unconstrained tile
                    tile = self.get_unconstrained_tile()
                    if tile is None:
                        board.inter.click(ls[0][0][0], ls[0][0][1])
                    else:
                        board.inter.click(tile[0], tile[1])

            else:                                       
                tile = self.get_unconstrained_tile()
                board.inter.click(tile[0], tile[1])
                
                    
    def check_if_unconstrainted(self, x, y):
        '''
        Check if a tile is unconstrained.
        '''

        if board.board[y][x] != UNOPENED:
            return False
        for g in self.groups:
            if (x, y) in g.coords:
                return False
        return True
    
    def get_unconstrained_tile(self):
        '''
        Get an unconstrained tile.
        '''

        # Check corners
        corners = [(0, 0), (board.width - 1, 0), (0, board.height - 1), (board.width - 1, board.height - 1)]
        for x, y in corners:
            if self.check_if_unconstrainted(x, y):
                return x, y

        # Check edges
        for x in range(1, board.width - 1):
            if self.check_if_unconstrainted(x, 0):
                return x, 0
            if self.check_if_unconstrainted(x, board.height - 1):
                return x, board.height - 1
        for y in range(1, board.height - 1):
            if self.check_if_unconstrainted(0, y):
                return 0, y
            if self.check_if_unconstrainted(board.width - 1, y):
                return board.width - 1, y
            
        # Check middle
        for x in range(1, board.width - 1):
            for y in range(1, board.height - 1):
                if self.check_if_unconstrainted(x, y):
                    return x, y
        
        # Cannot get an unconstrained tile
        return None

    def solve(self):
        '''
        Main solve loop.
        '''

        # First click
        board.inter.click(0, 0)

        # Generate solution sets
        self.gen_solution_sets()

        # Main loop
        while not board.is_done:

            # time.sleep(0.5)  # Optional delay 

            # Generate groups (again)
            self.gen_groups()

            # End loop if 'b' is pressed
            if keyboard.is_pressed('b'):
                board.has_won = False
                break

            # Perform solves
            if self.simple_solve():
                continue
            if self.group_solve():
                # print('Group solve')
                continue
            if self.subgroup_solve():
                # print('Subgroup solve')
                continue
            
            # Create coupled groups
            self.create_coupled_groups()
            
            # CSP solve
            if self.coupled_groups:
                # print('CSP solve')
                self.solve_coupled_groups()
            else:
                # It's a 50/50
                try:
                    board.inter.click(self.groups[0].coords[0][0], self.groups[0].coords[0][1])
                    # print('50/50 solve')
                except:
                    for i in range(board.width):
                        for j in range(board.height):
                            if board.board[j][i] == UNOPENED:
                                board.inter.click(i, j)
        
        if board.has_won:
            print('Solver won!')
        else:
            print('Solver lost!')
            
