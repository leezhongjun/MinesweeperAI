from interface import Interface
from solver import Solver
import board


INITIAL_MINES = 99
coords = [85, 189, 573, 454]
x_s = [5, 21, 37, 53, 69, 85, 101, 117, 133, 149, 165, 181, 197, 213, 229, 245, 261, 277, 293, 309, 325, 341, 357, 373, 389, 405, 421, 437, 453, 469]
y_s = [5, 18, 34, 50, 66, 82, 98, 114, 130, 146, 162, 178, 194, 210, 226, 242]

def main():
    board.remaining_mines = INITIAL_MINES
    board.inter = Interface(coords, x_s, y_s)
    board.inter.initial_init(do_get_frame_coords=True, do_get_img_coords=True)
    print(board.has_won, board.is_done)
    s = Solver()
    s.solve()


if __name__ == '__main__':
    main()