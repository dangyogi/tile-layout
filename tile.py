# tile.py

from math import sin, cos
from Pillow import Image

import app
from utils import my_eval, eval_pair, eval_color


def erase_tiles():
    app.canvas.delete("tile")

def generate_tile(name, shape, args, tile, colors, rotation=0):
    constants = args.copy()
    if 'constants' in shape:
        for name, exp in shape['constants'].items():
            constants[name] = my_eval(exp, constants)
    def get(name, eval_fn=my_eval):
        #print(f"get({name!r})")
        return eval_fn(shape[name], constants)
    if 'color' in tile:
        return Tile(name, get('points', eval_points), get('skip_x'), get('skip_y'),
                    color=eval_color(tile['color], colors))
    return Image_tile(name, get('points', eval_points), get('skip_x'), get('skip_y'),
                      image=tile['image'], rotation=rotation)

def eval_points(points, constants):
    return tuple(eval_pair(p, constants) for p in points)

def gen_tile(name, tile, shapes, colors):
    #print(f"Generating Tile {name!r}")
    if shapes is None:
        shapes = app.Shapes
    color = eval_color(tile['color'], colors)
    shape = shapes[tile['shape']]
    assert shape['type'] == 'polygon', f"expected type 'polygon', got '{shape['type']}'"
    args = {param: tile[param] for param in shape['parameters']}
    tile_1 = generate_tile(name, shape, args, tile, colors)
    yield name, tile_1
    if 'flipped' in shape:
        f = shape['flipped']
        if 'shape' in f:
            shape = shapes[f['shape']]
        args = {param: tile[arg_name]
                for param, arg_name
                 in zip(shape['parameters'], f['arguments'])}
        name += ' - flipped'
        tile_2 = generate_tile(name, shape, args, tile, colors, 90)
        yield name, tile_2
        tile_1.flipped = tile_2
        tile_2.flipped = tile_1


class Base_tile:
    def __init__(self, name, points, skip_x, skip_y):
        self.name = name
        self.points = points
        self.skip_x = skip_x
        self.skip_y = skip_y

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.name}>"


class Tile(Base_tile):
    def __init__(self, name, points, skip_x, skip_y, color):
        super().__init__(name, points, skip_x, skip_y)
        self.color = color

    def place_at(self, offset, plan):
        return plan.create_polygon(self.points, offset, self.color)


class Image_tile(Base_tile):
    def __init__(self, name, points, skip_x, skip_y, image_file, rotation):
        super().__init__(name, points, skip_x, skip_y)
        self.image_file = image_file
        self.image = Image.open(image_file)
        if 'A' not in self.image.getbands():
            self.image.putalpha(255)
        if rotation:
            self.image = self.image.rotate(rotation, expand=True)

        # offset from SW corner of image to first point in self.points
        self.sw_offset = -min(p[0] for p in self.points), -min(p[1] for p in self.points)

        # width and height in inches, based on self.points
        self.in_width = max(p[0] for p in self.points) + self.sw_offset[0]
        self.in_height = max(p[1] for p in self.points) + self.sw_offset[1]

        # The scaled image is stored in self.scaled_image based on current scale
        # in app.canvas.my_scale.  We can't scale now because the app is not fully
        # initialized yet when this is run.  Also, the scale will change if the
        # user resizes the window.  So we check the scale each time we're asked
        # to place the image, and recalc as necessary.
        self.scale = None

    def get_image(self, plan):
        r'''Returns sw_offset, image.

        The `sw_offset` is the offset from the SW corner of the image to the first
        point in self.points.

        Checks self.scale and recalcs self.scaled_image as necessary.  Also manages
        the cache of rotated images in self.cache, which is key-ed by the rotation
        angle and stores the rotated (sw_offset, image).
        '''
        # first, get self.scaled_image scaled to current app scale.
        if app.canvas.my_scale != self.scale:
            self.scale = app.canvas.my_scale
            self.scaled_image = self.image.resize((app.canvas.in_to_px(self.in_width),
                                                   app.canvas.in_to_px(self.in_height)))
            self.cache = {}

        # then get rotated image
        angle = plan.alignment.angle
        if angle not in self.cache:
            if angle == 0:
                rotated_image = self.scaled_image
                sw_offset = self.sw_offset
            else:
                rotated_image = self.scaled_image.rotate(angle, expand=True)

                # Calculate sw_offset:
                old_size = self.scaled_image.size
                old_center = old_size[0] / 2, old_size[1] / 2
                new_size = rotated_image.size
                new_center = new_size[0] / 2, new_size[1] / 2
                # adjust the old offset from the center of the image for the rotation
                old_offset_from_center = (self.sw_offset[0] - old_center[0],
                                          self.sw_offset[1] - old_center[1])
                new_offset = plan.alignment.rotate(old_offset_from_center)
                # translate new_offset to offset from SW corner
                sw_offset = (new_offset[0] + new_center[0],
                             new_offset[1] + new_center[1]))
            self.cache[angle] = sw_offset, rotated_image

        # return rotated image
        return self.cache[angle]

    def place_at(self, offset, plan):
        if plan.align(self.points, offset) is None:
            return False
        sw_offset, image = self.get_image(plan)
        plan.create_image(image, sw_offset, offset)
        return True
