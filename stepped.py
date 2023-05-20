# stepped.py

from itertools import islice, count, cycle

from utils import f_to_str


def stepped(tile, offset, grout_gap, angle, x_offset, y_offset, max_x, max_y):
    width = tile.width + grout_gap
    offsets = []
    for i in count(0):
        next = width * offset * i
        if abs(next) >= width:
            break
        offsets.append(next)
    stepped2(tile, offsets, grout_gap, angle, x_offset, y_offset, max_x, max_y)


def stepped2(tile, offsets, grout_gap, angle, x_offset, y_offset, max_x, max_y):
    width = tile.width + grout_gap
    def lay_row(left_start, bottom):
        visible = False

        # lay to the right
        #print(f"lay to right {f_to_str(left_start)=}, "
        #      f"{f_to_str(max_x + max_y)=}, {f_to_str((max_x + max_y) // width + 1)=}")
        for left in islice(count(left_start, width), (max_x + max_y) // width + 1):
            v = tile.place_at("ll", (left, bottom), angle, x_offset, y_offset,
                              max_x, max_y) is not None
            if v:
                visible = True
            #print(f"lay to right tried {f_to_str(left)=}, {v=}")

        # lay to the left
        #print(f"lay to left {f_to_str(left_start - width)=}, "
        #      f"{f_to_str(max_y)=}, {f_to_str(max_y // width + 1)=}")
        for left in islice(count(left_start - width, -width), max_y // width + 1):
            v = tile.place_at("ll", (left, bottom), angle, x_offset, y_offset,
                              max_x, max_y) is not None
            if v:
                visible = True
            #print(f"lay to left tried {f_to_str(left)=}, {v=}")

        return visible

    # lay up
    for row_num, left in zip(count(0), cycle(offsets)):
        if left > 0:
            left -= width
        #print("lay up", row_num, f_to_str(left),
        #      f_to_str(row_num * (tile.height + grout_gap)))
        if not lay_row(left, row_num * (tile.height + grout_gap)):
            break

    # lay down
    for row_num, left in zip(count(-1, -1), cycle(reversed(offsets))):
        left = -left
        #print("lay down", row_num, f_to_str(left),
        #      f_to_str(row_num * (tile.height + grout_gap)))
        if not lay_row(left, row_num * (tile.height + grout_gap)):
            break

