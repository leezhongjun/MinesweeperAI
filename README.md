# Minesweeper AI
Minesweeper AI solver that interfaces with minesweeperonline.com with OpenCV
Also works with the original winmine.exe (download [here](https://archive.org/download/BestOfWindowsEntertainmentPack64Bit))

## Demo
![minesweeper](https://user-images.githubusercontent.com/80515759/223396465-f083c093-dbbd-4cff-9a4c-a9b791040ebc.gif)

## Features
 - Fast screenshot with mss
 - Fast tile recognition with histograms
 - Brute force search as [Minesweeper is NP-complete](https://web.archive.org/web/20121018141147/http://www.claymath.org/Popular_Lectures/Minesweeper/)
 - Solve based on Minesweeper as a [Constraint Satisfaction Problem](https://en.wikipedia.org/wiki/Constraint_satisfaction_problem) with [coupled subsets](http://www.cs.toronto.edu/~cvs/minesweeper/minesweeper.pdf)


## Algorithm
 - First tile clicked is [corner tile](https://minesweepergame.com/math/exploring-efficient-strategies-for-minesweeper-2017.pdf)
 - Simple search 
    - Number of mines = value on tile - number of flags adjacent to tile
    - If number of mines == len(adjacent tiles): all adjacent tiles are mines
    - If number of mines == 0: all adjacent tiles are safe tiles
 - Group search
    - If one group (consisting of all unopened tiles adjacent to one tile) is a subset of another group:
        - If they have the same number of mines:
            - The difference between them are safe tiles
        - If the subset has X less mines than the other group and X == size of group that is the difference between them are safe tiles:
            - The difference between them are mines
 - Subgroup search
    - For each group:
        - Create a 'no more than' subgroup
        - Create an 'at least' subgroup
        - Perform safe and mine checks between each group and subgroup
 - Constraint Satisfaction Problem (CSP) search
    - Couple constraints together into a subset if they share a common variable
    - Solve for solutions to the coupled subset
    - Eliminate solutions with more mines than remaining mines
    - Calculate probability of a tile in subset being mine-free (based on all its possible solutions)
        - Calculate no of possible combinations of bombs with remaining tiles given a solution (use this as weight)
    - Calculate probability of an unconstrained tile being mine-free
        - Position of unconstrained tile in the order of corner, edge then internal tile

## Potential improvements
 - Neural network for tile classification

 ### Dependencies
 - pynput
 - pyautogui
 - opencv-python
 - [mss](https://pypi.org/project/mss/1.0.2/)
 - numpy
 - keyboard

### How to use
1. Modify `INITIAL_MINES` in `main.py`
1. Run `main.py`
2. Left click on upper left hand corner of board
3. Left click on lower right hand corner of board
Note: Press 'b' to terminate midway through loop

PS. modify `main.py` if you want it to remember the position of the board

 ### References
 - [Color appoximation with histograms](https://developershell.net/solving-minesweeper-part-9-color-separation/)
 - [Algorithmic Approaches to Playing Minesweeper (pdf)](https://dash.harvard.edu/bitstream/handle/1/14398552/BECERRA-SENIORTHESIS-2015.pdf)
 - [Minesweeper as a Constraint Satisfaction Problem (pdf)](http://www.cs.toronto.edu/~cvs/minesweeper/minesweeper.pdf)
 - [Exploring Efficient Strategies for Minesweeper (pdf)](https://minesweepergame.com/math/exploring-efficient-strategies-for-minesweeper-2017.pdf)
 - [gamescomputersplay/minesweeper-solver](https://github.com/gamescomputersplay/minesweeper-solver)

 
