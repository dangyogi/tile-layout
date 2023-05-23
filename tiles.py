# tiles.py

from utils import read_yaml
from tile import gen_tile


def read_tiles(shapes=None, colors=None, filename="tiles.yaml"):
    return {name: tile
            for tile_name, specs in read_yaml(filename).items()
            for name, tile in gen_tile(tile_name, specs, shapes, colors)}



if __name__ == "__main__":
    from pprint import pp
    from colors import read_colors
    from shapes import read_shapes

    colors = read_colors()
    shapes = read_shapes()

    def dump(name, tile):
        print(name)
        print("  name:", tile.name)
        print("  skip_x:", tile.skip_x)
        print("  skip_y:", tile.skip_y)
        print("  color:", tile.color)
        print("  points:", tile.points)
        if hasattr(tile, 'flipped'):
            print("  flipped:", tile.flipped.name)
        print()

    for name, tile in read_tiles(shapes, colors).items():
        dump(name, tile)
