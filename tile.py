# tile.py

from math import sin, cos

import app
from utils import f_to_str


def erase_tiles():
    app.canvas.delete("tile")
    Placement.Seen = set()


class Tile:
    flipped = None

    @classmethod
    def create(cls, name, width, height, color):
        ans = cls(name, width, height, color)
        if width != height:
            ans.flipped = cls(name + ' - flipped', height, width, color)
        return ans

    def __init__(self, name, width, height, color):
        self.name = name
        self.width = width
        self.height = height
        self.color = color

    def __str__(self):
        return f"<Tile: {self.name}>"

    def tiles(self):
        yield self
        if self.flipped is not None:
            yield self.flipped

    def place_at(self, corner, point, angle, max_x, max_y, test=False):
        r'''max_x and max_y are in inches.
        '''
        return Placement.create(self, corner, point, angle, max_x, max_y, test)


def rotate(point, angle):
    s, c = sin(angle), cos(angle)
    x, y = point
    return x * c - y * s, x * s + y * c

class Placement:
    Seen = set()
    #Count = 0

    def __init__(self, tile, left, top, angle=0, test=False):
        #print(f"{tile} placed at left={f_to_str(left)}, top={f_to_str(top)}")
        self.tile = tile
        self.left = left
        self.top = top
        if not test:
            item = app.myapp.create_polygon(self.tile.color,
                     rotate((self.left, self.bottom), angle),
                     rotate((self.right, self.bottom), angle),
                     rotate((self.right, self.top), angle),
                     rotate((self.left, self.top), angle),
                     tags=('tile',))
            app.canvas.tag_lower(item, "topmost")

    @classmethod
    def create(cls, tile, corner, point, angle, max_x, max_y, test):
        r'''max_x and max_y are in inches.
        '''
        x, y = point
        if corner == 'ul':
            left, top = x, y
        elif corner == 'ur':
            left, top = x - tile.width, y
        elif corner == 'll':
            left, top = x, y + tile.height
        elif corner == 'lr':
            left, top = x - tile.width, y + tile.height
        else:
            raise ValueError(f"Invalid corner: {corner!r}")
        points = [rotate((x, y), angle)
                  for x in (left, left + tile.width)
                  for y in (top - tile.height, top)]
        to_left, to_right, to_top, to_bottom = False, False, False, False
        for x, y in points:
            if x > 0: to_right = True
            if x < max_x: to_left = True
            if y > 0: to_top = True
            if y < max_y: to_bottom = True
        if not all((to_left, to_right, to_top, to_bottom)):
            return None
        if (tile, left, top) in cls.Seen:
            return None
        #if cls.Count > 50:
        #    return None
        #cls.Count += 1
        cls.Seen.add((tile, left, top))
        return cls(tile, left, top, angle, test)

    def __str__(self):
        return f"<Placement: {self.tile} at ({f_to_str(self.left)}, {f_to_str(self.top)})>"

    @property
    def right(self):
        return self.left + self.tile.width

    @property
    def bottom(self):
        return self.top - self.tile.height

    def at(self, corner, delta_X=0, delta_Y=0):
        r'''Returns point at corner.
        '''
        if corner == 'ul':
            return self.left + delta_X, self.top + delta_Y
        if corner == 'ur':
            return self.right + delta_X, self.top + delta_Y
        if corner == 'll':
            return self.left + delta_X, self.bottom + delta_Y
        if corner == 'lr':
            return self.right + delta_X, self.bottom + delta_Y
        raise ValueError(f"Invalid corner: {corner!r}")

