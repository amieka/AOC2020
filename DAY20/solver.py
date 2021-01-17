import os
import sys
import curses
import time
import threading
import traceback
from enum import Enum
from functools import lru_cache
from math import sqrt


class CornerType(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    RIGHT = "right"
    LEFT = "left"


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    MAGENTA = "\035[47m"
    RED = "\031[47m"
    LGRAY = "\033[37m"
    ORANGE = "\033[33m"
    BITSET = [153, 153, 153]
    BITUNSET = [176, 188, 188]
    BITSETSEAGREEN = [51, 127, 125]
    BITUNSETGREEN = [204, 255, 253]


def RGBToANSI(r, g, b):
    if r == g and g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return round(((r - 8) / 247) * 24) + 232
    return (
        16
        + (36 * round(r / 255 * 5))
        + (6 * round(g / 255 * 5))
        + round(b / 255 * 5)
    )


def ColoredText(rgb=[255, 255, 255]):
    return "\x1b[48;5;{}m \x1b[0m".format(
        int(RGBToANSI(rgb[0], rgb[1], rgb[2]))
    )


class Tile:
    def __init__(self, tile_id, orientation_id):
        self.orientation_id = orientation_id
        self.tile_id = tile_id
        self.raw_data = None
        self.block_size = 10
        self.trimmed_data = [
            ["."] * (self.block_size - 2) for _ in range(self.block_size - 2)
        ]
        self.corners = {}

    def update(self, data):
        self.raw_data = data

    def trim_corners(self):
        block_size = 10
        data = self.raw_data
        for r in range(1, block_size - 1):
            for c in range(1, block_size - 1):
                self.trimmed_data[r - 1][c - 1] = data[r][c]

    @property
    def orientations(self):
        return self.corners

    @property
    def grid_lines(self):
        return self.raw_data

    def rotate90(self):
        rows, ret = list(zip(*self.raw_data[::-1])), []
        for r in rows[::-1]:
            ret.append("".join(r[::-1]))
        return ret

    def flip_v(self):
        ret = []
        for row in self.raw_data:
            ret.append(row[::-1])
        return ret

    def update_corners(self, data):
        # print(data)
        edge_length = len(data[0])
        up, down, left, right = [], [], [], []
        for idx in range(edge_length):
            up.append(data[0][idx])
            down.append(data[edge_length - 1][idx])
            right.append(data[idx][edge_length - 1])
            left.append(data[idx][0])

        return {
            "up": "".join(up),
            "down": "".join(down),
            "right": "".join(right),
            "left": "".join(left),
        }

    def can_place_right(self, r, c, R, C, visited):
        if self.is_valid(r, c - 1, R, C) and visited[r][c - 1] is not None:
            second_tile = visited[r][c - 1]
            if self.tile_id != second_tile.tile_id:
                if self.orientations.get(
                    "left"
                ) == second_tile.orientations.get("right"):
                    return True
        return False

    def can_place_bottom(self, r, c, R, C, visited):
        if self.is_valid(r - 1, c, R, C) and visited[r - 1][c] is not None:
            second_tile = visited[r - 1][c]
            if self.tile_id != second_tile.tile_id:
                if self.orientations.get("up") == second_tile.orientations.get(
                    "down"
                ):
                    return True
        return False

    def is_valid(self, r, c, R, C):
        if r >= 0 and r < R and c >= 0 and c < R:
            return True
        return False


class Board:
    def __init__(self, file_name):
        self.visited = None
        self.R = -1
        self.C = -1
        self.current_r = 0
        self.current_c = 0
        self.tiles = []
        self.tiles_count = 0
        self.filled_grid = None
        self.raw_grid = None
        # holds the resized board as a Tile, so that
        # it can be rotated and flipped
        self.resized_grid = Tile("-1", "-1")
        self.block_size = 10
        self.read_layout(file_name)
        self.init_board()
        self.m_pattern = []

    def resize_board(self):
        for r in range(self.R):
            for c in range(self.C):
                tile = self.visited[r][c]
                tile.trim_corners()
                # expensive copy
                self.visited[r][c] = tile
        self.fill_grid(self.visited, False, 8, True, False)
        self.resized_grid.update(self.filled_grid)

    def read_layout(self, file_name):
        try:
            f = open(file_name, "r")
            tile_id, grid_lines, tile = None, [], None
            for line in f.readlines():
                if line == "\n":
                    continue
                if ":" in line:
                    if tile_id is not None:
                        for flips in range(2):
                            for rotation in range(4):
                                tile = Tile(
                                    tile_id, int(tile_id) + self.tiles_count
                                )
                                tile.update(grid_lines)
                                tile.corners.update(
                                    tile.update_corners(grid_lines)
                                )
                                self.tiles.append(tile)
                                grid_lines = tile.rotate90()
                                self.tiles_count += 1

                            grid_lines = tile.flip_v()
                        grid_lines = []
                    tile_id = line.split(":")[0].split(" ")[1]
                else:
                    grid_lines.append(line.strip())

            # take care of the last tile
            for flips in range(2):
                for rotation in range(4):
                    tile = Tile(tile_id, int(tile_id) + self.tiles_count)
                    tile.update(grid_lines)
                    tile.corners.update(tile.update_corners(grid_lines))
                    self.tiles.append(tile)
                    grid_lines = tile.rotate90()
                    self.tiles_count += 1
                grid_lines = tile.flip_v()

        except FileNotFoundError as error:
            print(f"File not found error {error}")

    def init_board(self):
        self.R, self.C = int(sqrt(self.tiles_count * 0.125)), int(
            sqrt(self.tiles_count * 0.125)
        )
        print(f"R: {self.R}, C: {self.C}")
        self.visited = [[None] * self.C for _ in range(self.R)]

    @property
    def layout(self):
        return self.visited

    def is_valid(self, r, c, R, C):
        if r >= 0 and r < R and c >= 0 and c < C:
            return True
        return False

    def search_monster(self):
        try:
            m_pattern = [
                "..................#.",
                "#....##....##....###",
                ".#..#..#..#..#..#...",
            ]
            sr, sc, R_, C_ = (
                3,
                20,
                len(self.resized_grid.raw_data),
                len(self.resized_grid.raw_data),
            )

            # convert raw grid in list of strings
            total_roughness = 0
            idx, grid_lines = 0, self.resized_grid.raw_data

            def compute_roughness(raw_data):
                grid_, total_roughness, sea_monsters = raw_data, 0, 0
                for r in range(R_):
                    p_ = ["." for _ in range(sr)]
                    for c in range(C_):
                        pattern_count = [0 for _ in range(sr)]
                        for l in range(sr):
                            p1_, num_matches = ["." for _ in range(sc)], 0
                            for m in range(sc):
                                if self.is_valid(r + l, c + m, R_, C_):
                                    if (
                                        m_pattern[l][m] == "#"
                                        and raw_data[r + l][c + m] == "#"
                                    ):
                                        p1_[m] = "O"
                                        num_matches += 1

                            # dont like hard coding the numbers
                            if num_matches in [1, 6, 8]:
                                pattern_count[l] = num_matches
                                p_[l] = "".join(p1_)

                            if (
                                len(pattern_count) == 3
                                and pattern_count[0] == 1
                                and pattern_count[1] == 8
                                and pattern_count[2] == 6
                            ):

                                sea_monsters += 1

                        if raw_data[r][c] == "#":
                            total_roughness += 1
                return (sea_monsters, total_roughness)

            while True:
                for f in range(2):
                    for r in range(4):
                        # check for a sea monster after orienting the grid
                        seamonsters, total_roughness = compute_roughness(
                            grid_lines
                        )
                        if seamonsters > 0:
                            return total_roughness - seamonsters * 15
                        grid_lines = self.resized_grid.rotate90()
                        self.resized_grid.update(grid_lines)

                    grid_lines = self.resized_grid.flip_v()
                    self.resized_grid.update(grid_lines)

        except FileNotFoundError as error:
            print(f"error finding file {error}")

    # probably needed for the second part
    def print_grid(self, grid, full_print=False):
        if not grid:
            raise Exception("Not a valid grid row")
        if not full_print:
            for row in range((self.current_r + 1) * self.block_size):
                cols = []
                for col in range((self.current_c + 1) * self.block_size):
                    cols.append(grid[row][col])
                print("".join(cols))
            return

        for row in grid:
            if not row:
                continue
            if isinstance(row, list):
                print("".join(row))
            else:
                print(row)

    def fill_grid_by_pos(
        self, grid, data, pos, colorize=True, color_corners=False
    ):
        r_start, r_end, c_start, c_end, content_length = (
            pos[0],
            pos[1],
            pos[2],
            pos[3],
            10,
        )
        i = 0
        for r in range(r_start, r_end):
            j = 0
            for c in range(c_start, c_end):
                if data[i][j] == "#":
                    grid[r][c] = (
                        ColoredText(Colors.BITSETSEAGREEN)
                        if colorize
                        else data[i][j]
                    )
                else:
                    grid[r][c] = (
                        ColoredText(Colors.BITUNSETGREEN)
                        if colorize
                        else data[i][j]
                    )
                # color corners if set
                if colorize and color_corners:
                    if i == 0 and j in range(0, content_length):
                        grid[r][c] = (
                            ColoredText([102, 102, 102])
                            if colorize
                            else data[i][j]
                        )

                    elif i == content_length - 1 and j in range(
                        0, content_length
                    ):
                        grid[r][c] = (
                            ColoredText([102, 102, 102])
                            if colorize
                            else data[i][j]
                        )
                    elif j == 0 and i in range(0, content_length):
                        grid[r][c] = (
                            ColoredText([102, 102, 102])
                            if colorize
                            else data[i][j]
                        )
                    elif j == content_length - 1 and i in range(
                        0, content_length
                    ):
                        grid[r][c] = (
                            ColoredText([102, 102, 102])
                            if colorize
                            else data[i][j]
                        )
                    else:
                        grid[r][c] = (
                            ColoredText([102, 102, 102])
                            if colorize
                            else data[i][j]
                        )
                j += 1
            i += 1

    def default_data(self):
        ret = []
        block_size = 10
        for r in range(block_size):
            cols = []
            for c in range(block_size):
                cols.append(".")
            ret.append("".join(cols))
        return ret

    def fill_grid(
        self,
        visited,
        should_print=False,
        block_size=10,
        trimmed_corners=False,
        colorize=True,
    ):
        grid = [
            ["."] * (self.C) * block_size for _ in range((self.R) * block_size)
        ]
        self.raw_grid = [
            ["."] * self.C * block_size for _ in range(self.R * block_size)
        ]
        grid_size = block_size * self.R  # its a square grid
        start_r = 0
        raw_data = self.default_data()
        for row in range(self.R):
            start_c = 0
            for col in range(self.C):
                tile = visited[row][col]
                if not tile:
                    continue
                if tile is not None:
                    if trimmed_corners and tile.trimmed_data is not None:
                        raw_data = tile.trimmed_data
                    else:
                        raw_data = tile.raw_data

                end_r, end_c = start_r + block_size, start_c + block_size
                self.fill_grid_by_pos(
                    grid, raw_data, [start_r, end_r, start_c, end_c], colorize
                )
                self.fill_grid_by_pos(
                    grid,
                    raw_data,
                    [start_r, end_r, start_c, end_c],
                    colorize,
                )
                start_c += block_size
            start_r += block_size

        # memory inefficient
        self.filled_grid = grid

    def debug_print(self, data, r, c):
        self.fill_grid(self.visited)
        block_size = 10
        start_r, start_c = r * block_size, c * block_size
        end_r, end_c = start_r + block_size, start_c + block_size
        self.fill_grid_by_pos(
            self.filled_grid, data, [start_r, end_r, start_c, end_c], True
        )
        """
            # Clears the console
            # Reference : https://en.wikipedia.org/wiki/ANSI_escape_code
            # Composed of 2 parts
            # First: 2 J (indicates clearing the entire screen) 
            # Second: 1 H puts the cursor back on row 1
        """
        print("\033[2J\033[1;1H")
        self.print_grid(self.filled_grid)
        time.sleep(0.1)

    def reset_state(self):
        self.current_r = self.R
        self.current_c = self.C

    def solve_r(self, r, c, checked=set(), cnt=0):
        R, C = self.R, self.C
        if r == R:
            answer = (
                int(self.visited[0][0].tile_id)
                * int(self.visited[0][C - 1].tile_id)
                * int(self.visited[R - 1][0].tile_id)
                * int(self.visited[R - 1][C - 1].tile_id)
            )
            print(f"answer {answer}")
            # reset state
            self.current_r, self.current_c = 0, 0
            print("searching for a sea monster")
            self.fill_grid(self.visited, True)
            self.resize_board()
            roughness = self.search_monster()
            print(f"roughness {roughness}")
            exit(0)

        for tile in self.tiles:
            tile_id = tile.tile_id
            if not tile_id in checked:
                tile_data = tile.raw_data
                if __DEBUG__:
                    self.current_r = r
                    self.current_c = c
                    self.debug_print(tile_data, r, c)
                if r > 0 and not tile.can_place_bottom(
                    r, c, self.R, self.C, self.visited
                ):
                    continue
                if c > 0 and not tile.can_place_right(
                    r, c, self.R, self.C, self.visited
                ):
                    continue

                self.visited[r][c] = tile
                checked.add(tile_id)

                if c == C - 1:
                    self.solve_r(r + 1, 0, checked, cnt + 1)
                else:
                    self.solve_r(r, c + 1, checked, cnt + 1)
                checked.remove(tile_id)

    def __call__(self):
        try:
            if not __SOLVE__:
                return
            print(f"solving puzzle now")
            self.solve_r(0, 0)

        except Exception as ex:
            print(f"Error solving the puzzle {ex}")
            traceback.print_exc(file=sys.stdout)


# Global Program flags
__SOLVE__ = True
__DEBUG__ = True


def read_input():
    try:
        board = Board("day_20_small.in")
        board()
    except FileNotFoundError as file_not_found_error:
        print(f"file not found error {file_not_found_error}")
    except Exception as exception:
        print(f"An exception occured solving the puzzle {exception}")


if __name__ == "__main__":
    read_input()
