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
   - Search for neighbors:
     - For every tile(call it first tile), for every other tile (call it second tile)
       - if firstTile.tile_id != secondTile.tile_id and firstTile is not already visited
       - Find neighbors
       - If there are exactly 2 neighbors, add them to your answer
       