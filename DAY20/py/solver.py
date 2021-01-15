import os
import sys
import curses
import time
import threading
from enum import Enum
from functools import lru_cache
from math import sqrt

__DEBUG__ = False


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


def print_grid(grid, color=None):
    if not grid:
        print("xxxxxxxxxx")
        return
    for row in grid:
        if isinstance(row, list):
            if color:
                print(f"{color}{''.join(row)}{Colors.ENDC}")
            else:
                print("".join(row))
        else:
            if color:
                print(f"{color}{row}{Colors.ENDC}")
            else:
                print(row)


class Tile:
    def __init__(self, tile_id, orientation_id):
        self.orientation_id = orientation_id
        self.tile_id = tile_id
        self.raw_data = None
        self.corners = {}

    def update(self, data):
        self.raw_data = data

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
        self.tiles = []
        self.tiles_count = 0
        self.read_layout(file_name)
        self.init_board()

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

    def is_valid(self, r, c):
        if r >= 0 and r < self.R and c >= 0 and c < self.C:
            return True
        return False

    def search_monster(self, pattern):
        pass

    # probably needed for the second part

    def solve_r(self, r, c, checked=set(), cnt=0):
        R, C = self.R, self.C
        if r == R:
            # print(f"total recursive calls {cnt}")
            print("simulation complete")
            print(
                self.visited[0][0].tile_id,
                self.visited[0][C - 1].tile_id,
                self.visited[R - 1][0].tile_id,
                self.visited[R - 1][C - 1].tile_id,
            )
            answer = (
                int(self.visited[0][0].tile_id)
                * int(self.visited[0][C - 1].tile_id)
                * int(self.visited[R - 1][0].tile_id)
                * int(self.visited[R - 1][C - 1].tile_id)
            )
            print(f"answer {answer}")
            exit(0)
        for tile in self.tiles:
            tile_id = tile.tile_id
            if not tile_id in checked:
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
            print(f"solving puzzle now")
            if __SOLVE__:
                self.solve_r(0, 0)
        except Exception as ex:
            print(f"Error solving the puzzle {ex}")
            print(ex.__traceback__())


def fill_grid_by_pos(grid, data, pos):
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
            if "#" in data[i][j] or "." in data[i][j]:
                # colorize the corner edges
                # up.append(data[0][idx])
                # down.append(data[edge_length - 1][idx])
                # right.append(data[idx][edge_length - 1])
                # left.append(data[idx][0])
                colored_data = ""
                if r == 0:
                    grid[r][c] = f"{Colors.ORANGE}{data[i][j]}{Colors.ENDC}"
                elif r == 9:
                    grid[r][c] = f"{Colors.ORANGE}{data[i][j]}{Colors.ENDC}"
                elif c == 0:
                    grid[r][c] = f"{Colors.ORANGE}{data[i][j]}{Colors.ENDC}"
                elif c == 9:
                    grid[r][c] = f"{Colors.ORANGE}{data[i][j]}{Colors.ENDC}"
                else:
                    grid[r][c] = f"{Colors.OKGREEN}{data[i][j]}{Colors.ENDC}"
            else:
                grid[r][c] = (
                    f"{Colors.OKBLUE}#{Colors.ENDC}"
                    if data[i][j] == "1"
                    else f"{Colors.OKBLUE}.{Colors.ENDC}"
                )
            j += 1
        i += 1


def fill_grid_generic(visited, tiles: dict):
    grid_size = 30
    blue_zeros = f"{Colors.OKBLUE}0{Colors.ENDC}"
    grid = [["."] * grid_size for _ in range(grid_size)]
    l = 10
    i, j = 0, 0
    start_r = 0
    for r in range(3):
        start_c = 0
        for c in range(3):
            j += 10
            tile_id = visited[r][c]
            if tile_id == -1:
                continue
            tile = tiles.get(tile_id)
            content = tile.grid_lines
            end_r, end_c = start_r + 10, start_c + 10
            fill_grid_by_pos(grid, content, [start_r, end_r, start_c, end_c])
            start_c += 10
        start_r += 10
    return grid
    # print_grid(grid, Colors.OKCYAN)


__SOLVE__ = True


def read_input():
    try:
        board = Board("day_20.in")
        board()
    except FileNotFoundError as file_not_found_error:
        print(f"file not found error {file_not_found_error}")
    except Exception as exception:
        print(f"An exception occured solving the puzzle {exception}")


if __name__ == "__main__":
    read_input()
