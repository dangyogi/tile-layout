# test_utils.py

from fractions import Fraction
import pytest

import utils


@pytest.fixture
def constants():
    return dict(a=1, b=2)

@pytest.fixture
def colors():
    return dict(a='#1', b='#2')


@pytest.mark.parametrize("s, value", (
    ('4', 4),
    ('1/4', Fraction(1, 4)),
    ('1.1/4', Fraction(5, 4)),
))
def test_fraction(s, value):
    assert utils.fraction(s) == value


@pytest.mark.parametrize("f, str", (
    (3, "3"),
    (-3, "-3"),
    (Fraction(1, 3), "1/3"),
    (Fraction(-1, 3), "-1/3"),
    (Fraction(4, 3), "1.1/3"),
    (Fraction(-4, 3), "-1.1/3"),
))
def test_f_to_str(f, str):
    assert utils.f_to_str(f) == str


@pytest.mark.parametrize("s, value", (
    ('4', 4),
    ('1/4', Fraction(1, 4)),
    ('1.1/4', Fraction(5, 4)),
    ('a', 1),
    ('b', 2),
))
def test_eval_num(s, constants, value):
    assert utils.eval_num(s, constants) == value


@pytest.mark.parametrize("s, value", (
    ('1.1/4', Fraction(5, 4)),
    ('a', 1),
    ('b + 1.1/4 - a', Fraction(9, 4)),
    (123, 123),
))
def test_my_eval(s, constants, value):
    assert utils.my_eval(s, constants) == value


@pytest.mark.parametrize("s, relaxed, value", (
    ('1.1/4, a', False, (Fraction(5, 4), 1)),
    ('a + 1/4, 79', False, (Fraction(5, 4), 79)),
    ('a + 1/4, a + b', False, (Fraction(5, 4), 3)),
    ('a + 1/4', True, Fraction(5, 4)),
    (123, True, 123),
))
def test_eval_pair(s, constants, relaxed, value):
    assert utils.eval_pair(s, constants, relaxed) == value


@pytest.mark.parametrize("s, value", (
    ('#123', '#123'),
    ('a', '#1'),
    ('white', 'white'),
))
def test_eval_color(s, colors, value):
    assert utils.eval_color(s, colors) == value
