# tile.py

from math import sqrt
import os.path
from PIL import Image, ImageTk

import app
from utils import my_eval, eval_pair, eval_color, f_to_str


def erase_tiles(canvas):
    canvas.delete("section")
    canvas.delete("tile")

def generate_tile(name, shape, args, color, image, rotation=0):
    constants = args.copy()
    if 'constants' in shape:
        for const_name, exp in shape['constants'].items():
            constants[const_name] = my_eval(exp, constants, f"<generate_tile({name})>")
    def get(attr, eval_fn=my_eval, default='fail'):
        #print(f"get({attr!r})")
        if default == 'fail':
            value = shape[attr]
        else:
            value = shape.get(attr, default)
        return eval_fn(value, constants, f"<generate_tile({name})>")
    if color is not None:
        return Tile(name, get('points', eval_points), get('skip_x'), get('skip_y'),
                    color, get('is_rect', default=False), shape, args)
    return Image_tile(name, get('points', eval_points), get('skip_x'), get('skip_y'),
                      image, rotation)

def eval_points(points, constants, location):
    return tuple(eval_pair(p, constants, location) for p in points)

def gen_tile(name, tile):
    #print(f"Generating Tile {name!r}")
    shape = app.Shapes[tile['shape']]
    assert shape['type'] == 'polygon', f"expected type 'polygon', got '{shape['type']}'"
    args = {param: my_eval(tile[param], {}, f"<gen_tile({name}) {param}>")
            for param in shape['parameters']}
    tile_1 = generate_tile(name, shape, args, eval_color(tile.get('color')), tile.get('image'))
    yield name, tile_1
    tile_2 = tile_1.flip()
    if tile_2 is not None:
        yield tile_2.name, tile_2


class Base_tile:
    def __init__(self, name, points, skip_x, skip_y):
        self.name = name
        self.points = points
        self.skip_x = skip_x
        self.skip_y = skip_y

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    def dump(self, name):
        print(name)
        print("  name:", self.name)
        print("  skip_x:", f_to_str(self.skip_x))
        print("  skip_y:", f_to_str(self.skip_y))
        print("  points:", f_to_str(self.points))
        if hasattr(self, 'color'):
            print("  color:", self.color)
        if hasattr(self, 'flipped'):
            print("  flipped:", self.flipped.name)
        print()

    def flip(self):
        return None


class Tile(Base_tile):
    r'''Polygon tiles.  Rectangles have a clip method.
    '''

    # for rectangles, these are the indexes for the four points:
    lower_left = 0
    upper_left = 1
    upper_right = 2
    lower_right = 3

    def __init__(self, name, points, skip_x, skip_y, color, is_rect, shape, args):
        super().__init__(name, points, skip_x, skip_y)
        self.color = color
        self.is_rect = is_rect and skip_x != skip_y
        if self.is_rect:
            self.alignment = 'horz' if skip_x > skip_y else 'vert'
        self.shape = shape
        self.args = args

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.name}, {self.color}>"

    def flip(self):
        shape = self.shape
        if 'flipped' in shape:
            f = shape['flipped']
            if 'shape' in f:
                shape = app.Shapes[f['shape']]
            args = {param: self.args[arg_name]
                    for param, arg_name
                     in zip(shape['parameters'], f['arguments'])}
            tile_2 = generate_tile(f"{self.name}-flipped", shape, args, self.color, None, 90)
            self.flipped = tile_2
            tile_2.flipped = self
            return tile_2
        return None

    def with_color(self, color):
        tk_color = eval_color(color)
        print(f"Tile({self.name}).with_color({color}) -> {tk_color=}")
        ans = Tile(f"{self.name}-{color}", self.points, self.skip_x, self.skip_y,
                   tk_color, self.is_rect, self.shape, self.args)
        ans.flip()
        return ans

    def clip(self, length, corner=None, grout_gap=None):
        r'''Clip the length (whether horizontal or vertical) and return a new Tile.

        If corner is None, the tile is simply shortened.

        Otherwise, corner is 'lower_left', 'lower_right', 'upper_left', or 'upper_right'
        and the tile is mitred at 45 degrees removing that corner.

        The `grout_gap` is only used if corner is not None.
        '''
        assert self.is_rect, f"Tile({self.name}).clip only allowed on rectangles"
        points = list(self.points)
        if corner is None:
            if self.alignment == 'horz':
                points[self.upper_right] = [length, self.skip_y]
                points[self.lower_right] = [length, 0]
                skip_x = length
                skip_y = self.skip_y
            else:
                points[self.upper_left] = [0, length]
                points[self.upper_right] = [self.skip_x, length]
                skip_x = self.skip_x
                skip_y = length
            ans = Tile(f"{self.name}-clipped", points, skip_x, skip_y, self.color, True,
                       self.shape, self.args)
            ans.flip()
            return ans
        if corner not in ('lower_left', 'lower_right', 'upper_left', 'upper_right'):
            raise ValueError(f"Tile({self.name}).clip: illegal corner, got {corner!r}, "
                             "expected 'lower_left', 'lower_right', 'upper_left', or "
                             "'upper_right'")
        grout_offset = grout_gap / sqrt(2)
        long_length = length - grout_offset
        short_length = long_length - min(self.skip_x, self.skip_y)
        if self.alignment == 'horz':
            if corner == 'lower_left':
                # this tile will sit on top of the upper left corner.
                points = [
                    [length - short_length, 0],   # lower_left
                    [grout_offset, self.skip_y],  # upper_left
                    [length, self.skip_y],        # upper_right
                    [length, 0],                  # lower_right
                ]
            elif corner == 'lower_right':
                # this tile will sit on top of the upper right corner.
                points[self.upper_right] = [long_length, self.skip_y]
                points[self.lower_right] = [short_length, 0]
            elif corner == 'upper_left':
                # this tile will sit on bottom of the lower left corner.
                points = [
                    [grout_offset, 0],                      # lower_left
                    [length - short_length, self.skip_y],   # upper_left
                    [length, self.skip_y],                  # upper_right
                    [length, 0],                            # lower_right
                ]
            else:  # corner == 'upper_right'
                # this tile will sit on bottom of the lower right corner.
                points[self.upper_right] = [short_length, self.skip_y]
                points[self.lower_right] = [long_length, 0]
            skip_x = length
            skip_y = self.skip_y
        else: # self.alignment == 'vert'
            if corner == 'lower_left':
                # this tile will sit to the right of the lower right corner.
                points = [
                    [0, length - short_length],   # lower_left
                    [0, length],                  # upper_left
                    [self.skip_x, length],        # upper_right
                    [self.skip_x, grout_offset],  # lower_right
                ]
            elif corner == 'lower_right':
                # this tile will sit to the left of the lower left corner.
                points = [
                    [0, grout_offset],                     # lower_left
                    [0, length],                           # upper_left
                    [self.skip_x, length],                 # upper_right
                    [self.skip_x, length - short_length],  # lower_right
                ]
            elif corner == 'upper_left':
                # this tile will sit to the right of the upper right corner.
                points[self.upper_left] = [0, short_length]
                points[self.upper_right] = [self.skip_x, long_length]
            else:  # corner == 'upper_right'
                # this tile will sit to the left of the upper left corner.
                points[self.upper_left] = [0, long_length]
                points[self.upper_right] = [self.skip_x, short_length]
            skip_x = self.skip_x
            skip_y = length
        ans = Tile(f"{self.name}-mitred", points, skip_x, skip_y, self.color, True,
                   self.shape, self.args)
        ans.flip()
        return ans

    def place_at(self, offset, angle, plan, skip):
        r'''The `angle` is ignored here.  Only used for Image_tiles.
        '''
        return plan.create_polygon(self.points, offset, self.color, skip)


class Image_tile(Base_tile):
    def __init__(self, name, points, skip_x, skip_y, image_file, rotation):
        super().__init__(name, points, skip_x, skip_y)
        self.image_file = image_file
        self.image = Image.open(os.path.join('images', image_file))
        if 'A' not in self.image.getbands():
            self.image.putalpha(255)
        if rotation:
            self.image = self.image.rotate(rotation, expand=True)

        # offset from SW corner of image to first point in self.points
        self.sw_offset = self.get_sw_offset(self.points)

        # width and height in inches, based on self.points
        self.in_width = max(p[0] for p in self.points) + self.sw_offset[0]
        self.in_height = max(p[1] for p in self.points) + self.sw_offset[1]

        # The scaled image is stored in self.scaled_image based on current scale
        # in app.canvas.my_scale.  We can't scale now because the app is not fully
        # initialized yet when this is run.  Also, the scale will change if the
        # user resizes the window.  So we check the scale each time we're asked
        # to place the image, and recalc as necessary.
        self.scale = None

    def get_sw_offset(self, points):
        return (points[0][0] - min(p[0] for p in points),
                points[0][1] - min(p[1] for p in points))

    def get_image(self, plan, angle, new_points):
        r'''Returns sw_offset, image.

        The `sw_offset` is the offset from the SW corner of the image to the first
        point in self.points.

        Checks self.scale and recalcs self.scaled_image as necessary.  Also manages
        the cache of rotated images in self.cache, which is key-ed by the rotation
        angle and stores the rotated (sw_offset, imageTk).
        '''
        # first, get self.scaled_image scaled to current app scale.
        if app.canvas.my_scale != self.scale:
            print(f"Image_tile({self.name}).get_image creating scaled image")
            self.scale = app.canvas.my_scale
            self.scaled_image = \
              self.image.resize((int(round(app.canvas.in_to_px(self.in_width))),
                                 int(round(app.canvas.in_to_px(self.in_height)))))
            self.cache = {}

        # then get rotated image
        target_angle = angle + plan.alignment.angle
        if target_angle not in self.cache:
            print(f"Image_tile({self.name}).get_image creating rotated image "
                  f"for angle {target_angle}")
            if target_angle == 0:
                rotated_image = self.scaled_image
                sw_offset = self.sw_offset
            else:
                rotated_image = self.scaled_image.rotate(target_angle, expand=True)
                sw_offset = self.get_sw_offset(new_points)
            print(f"get_image: sw_offset=({sw_offset[0]:.2f}, {sw_offset[1]:.2f})")
            self.cache[target_angle] = sw_offset, ImageTk.PhotoImage(rotated_image)

        # return rotated image
        return self.cache[target_angle]

    def place_at(self, offset, angle, plan, skip):
        new_points = plan.align(self.points, offset)
        if new_points is None:
            return False
        if not skip:
            sw_offset, image = self.get_image(plan, angle, new_points)
            plan.create_image(image, sw_offset, new_points[0])
        return True
