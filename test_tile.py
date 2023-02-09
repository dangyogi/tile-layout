# test_tile.py

import pytest
from fractions import Fraction

import tile


@pytest.fixture
def tile_a():
    return tile.Tile.create("tile_a", 1, 2, "black")


@pytest.fixture
def placement_a(tile_a):
    return tile.Placement(tile_a, 10, 20, 0, test=True)


def test_placement(placement_a, tile_a):
    assert placement_a.left == 10
    assert placement_a.right == 11
    assert placement_a.top == 20
    assert placement_a.bottom == 18
    assert placement_a.tile == tile_a


@pytest.mark.parametrize("corner, delta_X, delta_Y, answer", (
    ("ul", 0, 0, (10, 20)),
    ("ul", 1, 2, (11, 22)),
    ("ur", 0, 0, (11, 20)),
    ("ur", 0, -1, (11, 19)),
    ("ll", 0, 0, (10, 18)),
    ("lr", 0, 0, (11, 18)),
))
def test_placement_at(placement_a, corner, delta_X, delta_Y, answer):
    assert placement_a.at(corner, delta_X, delta_Y) == answer


@pytest.mark.parametrize("corner, point, angle, left, top", (
    ("ul", (10, 20), 0, 10, 20),
    ("ur", (10, 20), 0, 9, 20),
    ("ll", (10, 20), 0, 10, 22),
    ("lr", (10, 20), 0, 9, 22),
))
def test_place_at(tile_a, corner, point, angle, left, top):
    p = tile_a.place_at(corner, point, angle, 100, 100, test=True)
    assert p.left == left
    assert p.top == top


@pytest.mark.parametrize("corner, point, angle, max_x, max_y, success", (
    ("ul", (10, 20), 0, 10, 50, False),
    ("ul", (10, 20), 0, 11, 50, True),
    ("ul", (10, 20), 0, 50, 18, False),
    ("ul", (10, 20), 0, 50, 19, True),
    ("ul", (0, 20),  0, 50, 50, True),
    ("ul", (-1, 20), 0, 50, 50, False),
    ("ul", (10, 1),  0, 50, 50, True),
    ("ul", (10, 0),  0, 50, 50, False),
))
def test_place_at_None(tile_a, corner, point, angle, max_x, max_y, success):
    if success:
        assert tile_a.place_at(corner, point, angle, max_x, max_y, test=True) is not None
    else:
        assert tile_a.place_at(corner, point, angle, max_x, max_y, test=True) is None
