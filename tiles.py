# tiles.py

from utils import read_yaml, f_to_str
from tile import gen_tile


def read_tiles(filename="tiles.yaml"):
    return {name: tile
            for tile_name, specs in read_yaml(filename).items()
            for name, tile in gen_tile(tile_name, specs)}



if __name__ == "__main__":
    from pprint import pp
    from colors import read_colors
    from shapes import read_shapes

    import app

    app.Colors = read_colors()
    app.Shapes = read_shapes()

    for name, tile in read_tiles().items():
        tile.dump(name)
