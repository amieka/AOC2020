Problem Link - https://adventofcode.com/2020/day/20

(Draft)
- First Part
  #### Solution Description
  The first part of the problem requires us find the corner edges that has exactly 2 matching neighbors.

  #### Algorithm
   - Preprocessing Step : For ever tile read from the input source do the following:
     - Compute all the possible orientations (A total of 8 possibilities per tile)
       - Rotate 90 degress clockwise (Repeats 4 times)
       - Flip the tile content along X - AXIS and Rotate the flipped content 90 degress clockwise (Repeats 4 times)
       - Push them into an array
   - Search for neighbors using Backtracking:
     - The general idea here is to be able to place all the tiles in the grid satifying constraints as per the problem description

  - The solution:
   - While placing a tile on a valid (row, col) we need to make sure that the current tile's top edge matches with the bottom edge of the tile above it. Likewise the tiles left edge should match with the right edge of the tile left of it.
   - start by placing it in the top left corner
   - For every tile that is already not visited:
    - if the tile cannot be placed right of the last placed tile continue
    - if the tile cannot be placed bottom of the last placed tile continue
    - Recurse by moving columwise (0,0) -> (0, 1) -> (0, 2)
    - Increment row when there are no more colums to visit on that row and Recurse
    - Program exits when there are no more rows left to explore
       