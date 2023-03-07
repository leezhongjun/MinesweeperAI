from pynput.mouse import Listener, Button
import pyautogui
import cv2
import mss
import numpy as np

from board import UNOPENED, FLAG, BOMB
import board

class Interface():
    '''
    The interface is used to interact with the game.
    (send input, get game state, etc.)
    '''

    def __init__(self, coords=[], x_s=[], y_s=[]):
        self.coords = coords
        self.corners = ['upper left', 'lower right']
        self.presses = 0
        self.img = None
        self.y_s = y_s
        self.x_s = x_s
        self.tile_length = 0
        self.offset = 0
        self.width = 0
        self.height = 0
        self.folder = 'histogram_data'
        self.hists = []


    def get_frame_coords(self):
        '''
        Gets the coordinates of the frame of the board.
        '''

        print('Left click the upper left corner of grid.')
        print('Then left click the lower right corner of grid.')

        self.coords =[]
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
        '''
        Gets screenshot of the board.
        '''

        # Capture region of screen
        with mss.mss() as sct:
            region = {'top': self.coords[1], 'left': self.coords[0], \
                    'width': self.coords[2] - self.coords[0], \
                    'height': self.coords[3] - self.coords[1]}
            sct_img = sct.grab(region)
            # Convert to np array
            img = np.array(sct_img)
            self.img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    def get_img_coords(self):
        '''
        Gets the coordinates of each tile in the board.
        Only call this once at the beginning of the game.
        '''

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
            
        # print(f'x_s: {x_s}')
        # print(f'y_s: {y_s}')

        # Save x and y coord arrays
        self.x_s = x_s
        self.y_s = y_s
        

    def calc_hist(self, x, y):
        '''
        Calculates the histogram of a tile.
        '''

        cropped = self.img[self.y_s[y] : self.y_s[y] + self.tile_length, \
                           self.x_s[x] : self.x_s[x] + self.tile_length]
        
        # cv2.imshow(f'{tile_x},{tile_y}',cropped)
        # cv2.waitKey(0)

        hist = cv2.calcHist([cropped],[0],None,[256],[0,256])
        return hist

    def load_hist(self, name):
        '''
        Loads a histogram from a file.
        '''

        res =  np.loadtxt(f'{self.folder}/{name}.txt').reshape(256,1)
        return res

    def load_hists(self):
        '''
        Loads all histograms from files (in the folder).
        '''

        # 9 is unopened tile
        # 10 is flag
        # 11 is bomb
        self.hists = [self.load_hist(i) for i in range(12)]

    def recognise(self, x, y):
        '''
        Recognises the tile at the given coordinates.
        '''

        h = self.calc_hist(x, y)
        minimum = 100000
        for i, hist in enumerate(self.hists):
            res = np.linalg.norm(hist - h)
            if res < minimum:
                minimum = res
                val = i
        return val


    def init_board(self):
        '''
        Initialises the board, setting all board tiles to their values.
        '''

        # Initialise board and unopened tiles
        b = [[] for _ in range(self.height)]
        board.unopened_tiles = self.width * self.height

        # Set all tiles to their values
        for i in range(self.height):
            for j in range(self.width):
                tile = self.recognise(j, i)

                if tile != UNOPENED:
                    board.unopened_tiles -= 1
                    if tile == BOMB:
                        board.has_won = False
                        board.is_done = True
        
                b[i].append(tile)

        return b


    def print_board(self):
        '''
        Prints the board
        '''

        for i in range(self.height):
            for j in range(self.width):
                if board.board[i][j] == UNOPENED:
                    print(' ', end=' ')
                else:
                    print(board.board[i][j], end=' ')
            print()


    def save_hist(self, x, y, num):
        '''
        Saves the histogram of a tile at the given coordinates to a file.
        '''

        h = self.calc_hist(x, y)
        np.savetxt(f'{self.folder}/{num}.txt', h)


    def click(self, x, y):
        '''
        Clicks on a tile at the given coordinates.
        '''

        if board.board[y][x] == UNOPENED:
            pyautogui.click(self.x_s[x] + self.coords[0] + self.offset, \
                            self.coords[1] +self. y_s[y] + self.offset)
            
            # Update board
            self.update_board()


    def flag(self, x, y):
        '''
        Flags a tile at the given coordinates.
        '''

        if board.board[y][x] == UNOPENED:
            pyautogui.click(self.x_s[x] + self.coords[0] + self.offset, \
                            self.coords[1] + self.y_s[y] + self.offset, button='right')
            
            # Update board
            board.board[y][x] = FLAG
            board.remaining_mines -= 1
            board.unopened_tiles -= 1
            if board.unopened_tiles == 0:
                board.is_done = True


    def initial_init(self, do_get_frame_coords=True, do_get_img_coords=True):
        '''
        Initialises the interface, 
        getting the frame coordinates 
        and image coordinates.
        '''

        if do_get_frame_coords:
            self.get_frame_coords()
        self.capture_screenshot()
        if do_get_img_coords:
            self.get_img_coords()

        # Save width, height, length of tile
        self.tile_length = self.x_s[1] - self.x_s[0]
        self.offset = (self.x_s[1] - self.x_s[0]) // 2
        self.width = len(self.x_s)
        self.height = len(self.y_s)

        self.load_hists()

        board.width = self.width
        board.height = self.height
        board.board = self.init_board()
    

    def update_board(self):
        '''
        Updates the board,
        and if the game is won, 
        or game is done.
        '''

        # Recapture screenshot
        self.capture_screenshot()

        done = True
        for i in range(self.height):
            for j in range(self.width):
                if board.board[i][j] == UNOPENED:
                    board.board[i][j] = self.recognise(j, i)

                    # Change in board: game not done
                    if board.board[i][j] != UNOPENED:
                        board.unopened_tiles -= 1
                        done = False
                        
                        # End game if bomb found
                        if board.board[i][j] == BOMB:
                            board.has_won = False
                            board.is_done = True
                            return
        
        # If no unopened tiles, game is done
        if board.unopened_tiles == 0:
            board.is_done = True
        else:
            board.is_done = done
        return