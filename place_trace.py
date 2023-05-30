# place_trace.py

import app
from utils import f_to_str


In_per_char = 8


def pt_init():
    global Diag, Wall_stats
    Diag = int((app.Wall.diagonal + 30) // In_per_char)
    Wall_stats = [[0] * 2 * Diag for _ in range(2 * Diag)]
    print(f"pt_init: diagonal={app.Wall.diagonal}, {len(Wall_stats)=}, {len(Wall_stats[0])=}")


def place(offset, visible):
    global Wall_stats
    if visible:
        flag = 2
    else:
        flag = 1
    x_index = int(offset[0] // In_per_char) + Diag
    y_index = Diag - int(offset[1] // In_per_char)
    if 0 <= y_index < len(Wall_stats) and 0 <= x_index < len(Wall_stats[0]):
        Wall_stats[y_index][x_index] |= flag
    #else:
    #    print(f"place_trace.place: offset {f_to_str(offset)} out of bounds "
    #          f"{x_index=}, {y_index=}")


def dump_stats():
    for row in Wall_stats:
        print(''.join(to_char(i) for i in row))


def to_char(i):
    return chr(ord('0') + i)
