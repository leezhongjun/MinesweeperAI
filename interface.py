from pynput.mouse import Listener, Button
import pyautogui
import cv2
import mss
import numpy as np

from board import UNOPENED, FLAG, BOMB
import board

class Interface():
    def __init__(self, coords=[]):
        self.coords = coords
        self.corners = ['upper left', 'lower right']
        self.presses = 0
        self.img = None
        self.y_s = []
        self.x_s = []
        self.tile_length = 0
        self.offset = 0
        self.width = 0
        self.height = 0
        self.folder = 'histogram_data'
        self.hists = []

    def get_frame_coords(self):
        print('Left click the upper left corner of grid')
        print('Then left click the lower right corner of grid')
        def on_click(x, y, button, pressed):
            if pressed and button == Button.left:
                print(f'Mouse clicked at ({x}, {y}) for {self.corners[self.presses]} corner')
                self.coords.extend((x, y))
                self.presses += 1
                return self.presses < 2
            if not pressed:
                return True

        with Listener(on_click=on_click) as l:
            l.join()

    def capture_screenshot(self):
        # Capture entire screen
        with mss.mss() as sct:
            region = {'top': self.coords[1], 'left': self.coords[0], \
                    'width': self.coords[2] - self.coords[0], \
                    'height': self.coords[3] - self.coords[1]}
            sct_img = sct.grab(region)
            # Convert to np array
            img = np.array(sct_img)
            self.img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def get_img_coords(self):
        ### Call only once to get the coordinates of tiles ###

        # Get the initial corner pixel locations using goodFeaturesToTrack
        corners = cv2.goodFeaturesToTrack(self.img, 0, 0.01, 10)
        corners = np.intp(corners)

        # Get y values
        idx = np.lexsort((corners[:, :, 0].ravel(), corners[:, :, 1].ravel()))
        sorted_corners = corners[idx]
        prev = sorted_corners[0,0,1]
        total = 0
        c = 0
        y_s = []
        for corner in sorted_corners:
            x, y = corner.ravel()
            if (y - prev) < 4:
                total += y
                c += 1
            else:
                y_s.append(round(total/c))
                total = y
                c = 1
            prev = y

        # Get x values
        idx = np.lexsort((corners[:, :, 1].ravel(), corners[:, :, 0].ravel()))
        sorted_corners = corners[idx]
        prev = sorted_corners[0,0,0]
        total = 0
        c = 0
        x_s = []
        for corner in sorted_corners:
            x, y = corner.ravel()
            if (x - prev) < 4:
                total += x
                c += 1
            else:
                x_s.append(round(total/c))
                total = x
                c = 1
            prev = x
        
        # Save width, height, length of tile
        self.x_s = x_s
        self.y_s = y_s
        self.tile_length = x_s[1] - x_s[0]
        self.offset = (x_s[1] - x_s[0]) // 2
        self.width = len(x_s)
        self.height = len(y_s)


    def calc_hist(self, x, y):
        cropped = self.img[self.y_s[y] : self.y_s[y] + self.tile_length, \
                           self.x_s[x] : self.x_s[x] + self.tile_length]
        # cv2.imshow(f'{tile_x},{tile_y}',cropped)
        # cv2.waitKey(0)
        hist = cv2.calcHist([cropped],[0],None,[256],[0,256])
        return hist

    def load_hist(self, name):
        res =  np.loadtxt(f'{self.folder}/{name}.txt').reshape(256,1)
        return res

    def load_hists(self):
        # 9 is unopened tile
        # 10 is flag
        # 11 is bomb
        self.hists = [self.load_hist(i) for i in range(12)] 

    def recognise(self, x, y):
        h = self.calc_hist(x, y)
        minimum = 100000
        for i, hist in enumerate(self.hists):
            res = np.linalg.norm(hist - h)
            if res < minimum:
                minimum = res
                val = i
        return val


    def init_board(self):
        b = [[] for _ in range(self.height)]
        for i in range(self.height):
            for j in range(self.width):
                b[i].append(self.recognise(j, i))
        board.unopened_tiles = self.width * self.height
        return b

    def print_board(self):
        for i in range(self.height):
            for j in range(self.width):
                if board.board[i][j] == UNOPENED:
                    print(' ', end=' ')
                else:
                    print(board.board[i][j], end=' ')
            print()


    def save_hist(self,x, y, num):
        h = self.calc_hist(x, y)
        np.savetxt(f'{self.folder}/{num}.txt', h)


    def click(self, x, y):
        if board.board[y][x] == UNOPENED:
            pyautogui.click(self.x_s[x] + self.coords[0] + self.offset, \
                            self.coords[1] +self. y_s[y] + self.offset)
            self.update_board()

    def flag(self, x, y):
        
        if board.board[y][x] == UNOPENED:
            pyautogui.click(self.x_s[x] + self.coords[0] + self.offset, \
                            self.coords[1] + self.y_s[y] + self.offset, button='right')
            board.board[y][x] = FLAG
            board.remaining_mines -= 1
            board.unopened_tiles -= 1
            if board.unopened_tiles == 0:
                board.is_done = True

    def initial_init(self, get_coords=True):
        if get_coords:
            self.get_frame_coords()
        self.capture_screenshot()
        self.get_img_coords()
        self.load_hists()
        board.width = self.width
        board.height = self.height
        board.board = self.init_board()
    
    def update_board(self):
        '''returns (game is won, game is done)'''
        self.capture_screenshot()
        done = True
        for i in range(self.height):
            for j in range(self.width):
                if board.board[i][j] == UNOPENED:
                    board.board[i][j] = self.recognise(j, i)
                    # change in board: game not done
                    if board.board[i][j] != UNOPENED:
                        board.unopened_tiles -= 1
                        done = False
                    elif board.board[i][j] == BOMB:
                        board.has_won = False
                        board.is_done = True
                        return
        
        board.has_won = True
        if board.unopened_tiles == 0:
            board.is_done = True
        else:
            board.is_done = done
        return
    
# coords =[56, 188, 545, 452]
# x_s, y_s, tile_length = ([6, 22, 38, 54, 70, 86, 102, 118, 134, 150, 166, 182, 198, 214, 230, 246, 262, 278, 294, 310, 326, 342, 358, 374, 390, 406, 422, 438, 454, 470], [6, 19, 35, 51, 67, 83, 99, 115, 131, 147, 163, 179, 195, 211, 227, 243], 16)
# offset = tile_length //2
# FOUND = True

# inter = Interface()
# inter.initial_init()
# # print(len(board.board), len(board.board[0]))
# inter.print_board()

# # print('sleeping')
# # import time
# # time.sleep(5)
# # print('done sleeping')
# inter.click(0,0)
# inter.update_board()
# # print(len(board.board), len(board.board[0]))
# inter.print_board()
