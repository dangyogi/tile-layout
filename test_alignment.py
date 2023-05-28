# test_alignment.py

from math import sqrt
import pytest
from pytest import approx

from alignment import Alignment


def mk_alignment(angle=0, offset=(0, 0)):
    return Alignment(dict(angle=angle, x_offset=offset[0], y_offset=offset[1]), {})


@pytest.mark.parametrize("pt, angle, value", (
    ((0, 0), 0, (0, 0)),
    ((0, 0), 90, (0, 0)),
    ((0, 0), -90, (0, 0)),
    ((0, 0), 45, (0, 0)),
    ((0, 0), -45, (0, 0)),
    ((0, 0), 15, (0, 0)),
    ((0, 0), -15, (0, 0)),

    ((0, 1), 0, (0, 1)),
    ((0, 1), 90, (-1, 0)),
    ((0, 1), -90, (1, 0)),
    ((0, 1), 45, (-sqrt(2)/2, sqrt(2)/2)),
    ((0, 1), -45, (sqrt(2)/2, sqrt(2)/2)),
    ((0, 1), 30, (-0.5, sqrt(3)/2)),
    ((0, 1), -30, (0.5, sqrt(3)/2)),

    ((1, 0), 0, (1, 0)),
    ((1, 0), 90, (0, 1)),
    ((1, 0), -90, (0, -1)),
    ((1, 0), 45, (sqrt(2)/2, sqrt(2)/2)),
    ((1, 0), -45, (sqrt(2)/2, -sqrt(2)/2)),
    ((1, 0), 30, (sqrt(3)/2, 0.5)),
    ((1, 0), -30, (sqrt(3)/2, -0.5)),

    ((1, 1), 0, (1, 1)),
    ((1, 1), 90, (-1, 1)),
    ((1, 1), -90, (1, -1)),
    ((1, 1), 45, (0, sqrt(2))),
    ((1, 1), -45, (sqrt(2), 0)),
    ((1, 1), 15, (sqrt(2) * 0.5, sqrt(2) * sqrt(3)/2)),
    ((1, 1), -15, (sqrt(2) * sqrt(3)/2, sqrt(2) * 0.5)),
))
def test_rotate(pt, angle, value):
    alignment = mk_alignment(angle=angle)
    rotated = alignment.rotate(pt)
    assert rotated == approx(value)
    assert alignment.align_pt(pt) == approx(rotated)
    assert alignment.unrotate(rotated) == approx(pt)
    assert alignment.unalign_pt(rotated) == approx(pt)
    for x in 0, 0.5, -0.5:
        for y in 0, 0.5, -0.5:
            alignment = mk_alignment(angle=angle, offset=(x, y))
            aligned = alignment.align_pt(pt)
            assert aligned == approx((value[0] + x, value[1] + y))
            assert alignment.unalign_pt(aligned) == approx(pt)


@pytest.mark.parametrize("x", (0, 1, -1))
@pytest.mark.parametrize("y", (0, 1, -1))
@pytest.mark.parametrize("x_offset", (0, 0.5, -0.5))
@pytest.mark.parametrize("y_offset", (0, 0.5, -0.5))
def test_offset(x, y, x_offset, y_offset):
    pt = x, y
    alignment = mk_alignment(offset=(x_offset, y_offset))
    aligned = alignment.align_pt(pt)
    assert aligned == approx((x + x_offset, y + y_offset))
    assert alignment.unalign_pt(aligned) == approx(pt)

