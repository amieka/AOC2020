import os
import sys
import curses
import time
import threading
from enum import Enum
from functools import lru_cache


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
    LGRAY = "\037[40m"


def print_grid(grid, color):
    if not grid:
        print("xxxxxxxxxx")
        return
    for row in grid:
        if isinstance(row, list):
            print(f"{color}{''.join(row)}{Colors.ENDC}")
        else:
            print(f"{color}{row}{Colors.ENDC}")


class Tile:
    def __init__(self, tile_id):
        self.tile_id = tile_id
        self.content = []
        self.raw_data = []
        self.transformations = {}
        self.orientations = []
        self.taken = False

    @property
    def grid_lines(self):
        return self.content

    def update(self, content):
        self.raw_data = content
        self.to_bitmask(content)
        self.transform()

    def rotate90(self, data, clockwise=True):
        if not data:
            return []

        ret = []
        rows = list(zip(*data[::-1]))
        if not clockwise:
            for r1 in rows[::-1]:
                ret.append("".join(r1[::-1]))
        else:
            for r in rows:
                ret.append("".join(r))

        return ret

    def flip_v(self, data, vertical=True):
        ret = []
        if vertical:
            for row in data:
                ret.append(row[::-1])
        else:
            return data[::-1]
        return ret

    def compute_checksum(self, row):
        checksum, idx = 0, 0
        # compresses 1101101000
        # into 872
        for data in row[::-1]:
            checksum += int(data) << idx
            idx += 1
        return checksum

    def to_bitmask(self, content):
        masks = []
        # converts ##.##.#...
        # into a binary string
        # 1101101000
        for row in content:
            cols = []
            for c in row:
                if c == ".":
                    cols.append("0")
                else:
                    cols.append("1")
            masks.append("".join(cols))
        self.content = masks
        return masks

    def edge(self, data):
        edge_length = len(data[0])
        up, down, left, right = [], [], [], []
        for idx in range(edge_length):
            up.append(data[0][idx])
            down.append(data[edge_length - 1][idx])
            right.append(data[idx][edge_length - 1])
            left.append(data[idx][0])

        return {
            "up": self.compute_checksum(up),
            "down": self.compute_checksum(down),
            "right": self.compute_checksum(right),
            "left": self.compute_checksum(left),
        }

    def transform(self):
        # append the original orientation as is
        # original.append(self.edge(self.content))
        # self.orientations.append(self.edge(self.content))

        r_content = self.content
        r_original = self.raw_data
        for i in range(4):
            t, t1 = self.rotate90(r_content), self.rotate90(r_original)
            r_content, r_original = t, t1
            self.orientations.append(self.edge(t))
            self.transformations[i] = t1

        f_content = self.flip_v(self.content)
        f_original = self.flip_v(self.raw_data)
        for i in range(4):
            t, t1 = self.rotate90(f_content), self.rotate90(f_original)
            f_content, f_original = t, t1
            self.orientations.append(self.edge(t))
            self.transformations[i + 4 + 1] = t1

    def debug_(self, orientation_id, visited, tiles_pair, pos):
        if self.transformations.get(orientation_id) is not None:
            orientation_data = self.transformations.get(orientation_id)
            # reset terminal
            print("\033[2J\033[1;1H")
            full_grid = fill_grid_generic(visited, tiles_pair)
            start_r, start_c = pos[0] * 10, pos[1] * 10
            end_r, end_c = start_r + 10, start_c + 10
            fill_grid_by_pos(
                full_grid, orientation_data, [start_r, end_r, start_c, end_c]
            )
            # print_grid(orientation_data, Colors.OKGREEN)
            print_grid(full_grid, Colors.OKGREEN)
            time.sleep(0.1)

    def can_place_left(self, r, c, visited, tiles_pair):
        if self.is_valid(r, c - 1) and visited[r][c - 1] != -1:
            second_tile_id = visited[r][c - 1]
            matching_orientations = tiles_pair.get(second_tile_id).orientations
            orientation_id = 0
            if self.tile_id != second_tile_id:
                for o1 in self.orientations:
                    orientation_id += 1
                    self.debug_(orientation_id, visited, tiles_pair, [r, c])
                    for o2 in matching_orientations:
                        if o1.get("left") == o2.get("right"):
                            return True
        return False

    def can_place_top(self, r, c, visited, tiles_pair):
        if self.is_valid(r - 1, c) and visited[r - 1][c] != -1:
            second_tile_id = visited[r - 1][c]
            matching_orientations = tiles_pair.get(second_tile_id).orientations
            orientation_id = 0
            if self.tile_id != second_tile_id:
                for o1 in self.orientations:
                    orientation_id += 1
                    self.debug_(orientation_id, visited, tiles_pair, [r, c])
                    for o2 in matching_orientations:
                        if o1.get("up") == o2.get("down"):
                            return True

        return False

    def is_valid(self, r, c):
        if r >= 0 and r < 3 and c >= 0 and c < 3:
            return True
        return False


class Board:
    def __init__(self, tiles_pair):
        self.visited = [[-1] * 3 for _ in range(3)]
        self.R = 3
        self.C = 3
        self.filled = 0
        self.tiles_pair = tiles_pair

    @property
    def layout(self):
        return self.visited

    @property
    def tiles(self):
        return self.tiles_pair

    def is_valid(self, r, c):
        if r >= 0 and r < self.R and c >= 0 and c < self.C:
            return True
        return False

    def search_monster(self, pattern):
        pass

    def search_all(self):
        center_configurations = self.solve_other(4, False)
        for tile in center_configurations:
            tile_id = tile.get("node")
            tile_edges = tile.get("edges")

    # probably needed for the second part

    def solve(self, r1, c1):
        def solve_r(r, c, running_tile_id=-1, checked=set(), cnt=0):
            R, C = 3, 3
            # print(f"solve({r,c})")
            print(f"total recursive calls {cnt}")
            if r == R:
                return
            for tile_id, tile in self.tiles_pair.items():

                if not tile_id in checked:
                    running_tile_id = tile_id
                    if r > 0 and not tile.can_place_top(
                        r, c, self.visited, self.tiles_pair
                    ):
                        continue
                    if c > 0 and not tile.can_place_left(
                        r, c, self.visited, self.tiles_pair
                    ):
                        continue

                    self.visited[r][c] = tile_id
                    checked.add(tile_id)

                    if c == C - 1:
                        nr, nc = r + 1, 0
                        solve_r(nr, nc, running_tile_id, checked, cnt + 1)
                    else:
                        nr, nc = r, c + 1
                        solve_r(nr, nc, running_tile_id, checked, cnt + 1)
                    checked.discard(tile_id)

        solve_r(0, 0)


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
                grid[r][c] = data[i][j]
            else:
                grid[r][c] = "#" if data[i][j] == "1" else "."
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


def read_input():
    try:
        f = open("day_20_small.in", "r")
        tiles = []
        tiles_pair = {}
        tile_id, grid_lines, tile, board = None, [], None, None
        for line in f.readlines():
            if line == "\n":
                continue

            if ":" in line:
                if tile_id is not None:
                    tile.update(grid_lines)
                    tiles_pair[tile_id] = tile
                    grid_lines = []
                tile_id = line.split(":")[0].split(" ")[1]
                tile = Tile(tile_id)
                tiles_pair[tile_id] = None
            else:
                grid_lines.append(line.strip())

        # fill in the last tile
        tile = Tile(tile_id)
        tile.update(grid_lines)
        tiles_pair[tile_id] = tile

        if tiles is not None:
            board = Board(tiles_pair)

        board.solve(0, 0)
        print(board.layout)
        print_grid_generic(board.layout, board.tiles)
    except FileNotFoundError as file_not_found_error:
        print(f"file not found error {file_not_found_error}")
    except Exception as exception:
        print(f"An exception occured solving the puzzle {exception}")


if __name__ == "__main__":
    read_input()
