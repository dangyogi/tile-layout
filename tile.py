# tile.py

from math import sin, cos

import app
from utils import my_eval, eval_pair, eval_color


def erase_tiles():
    app.canvas.delete("tile")

def generate_tile(name, shape, args, color):
    constants = args.copy()
    if 'constants' in shape:
        for name, exp in shape['constants'].items():
            constants[name] = my_eval(exp, constants)
    def get(name, eval_fn=my_eval):
        #print(f"get({name!r})")
        return eval_fn(shape[name], constants)
    return Tile(name, get('points', eval_points), get('skip_x'), get('skip_y'), color)

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
    tile_1 = generate_tile(name, shape, args, color)
    yield name, tile_1
    if 'flipped' in shape:
        f = shape['flipped']
        if 'shape' in f:
            shape = shapes[f['shape']]
        args = {param: tile[arg_name]
                for param, arg_name
                 in zip(shape['parameters'], f['arguments'])}
        name += ' - flipped'
        tile_2 = generate_tile(name, shape, args, color)
        yield name, tile_2
        tile_1.flipped = tile_2
        tile_2.flipped = tile_1


class Tile:
    def __init__(self, name, points, skip_x, skip_y, color):
        self.name = name
        self.points = points
        self.skip_x = skip_x
        self.skip_y = skip_y
        self.color = color

    def __str__(self):
        return f"<Tile: {self.name}>"

    def place_at(self, offset, plan):
        return plan.create_polygon(self.points, offset, self.color)

