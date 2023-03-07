from interface import Interface
from solver import Solver
import board


INITIAL_MINES = 10

def main():
    board.remaining_mines = INITIAL_MINES
    board.inter = Interface()
    board.inter.initial_init()
    s = Solver()
    s.solve()


if __name__ == '__main__':
    main()