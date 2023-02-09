# tiles.py

from utils import read_csv, eval_num, eval_color
from tile import Tile


def read_tiles(colors, filename="tiles.csv"):
    tiles = {}
    for name, height, width, color in read_csv(filename):
        tile = Tile.create(name, eval_num(width, {}), eval_num(height, {}),
                           eval_color(color, colors))
        for t in tile.tiles():
            tiles[t.name] = t
    return tiles



if __name__ == "__main__":
    from pprint import pp

    pp(read_tiles(dict(a='#1', b='#2')))
