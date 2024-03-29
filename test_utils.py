# test_utils.py

from fractions import Fraction
import pytest
from unittest.mock import Mock

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
    ('-4', -4),
    ('-1/4', Fraction(-1, 4)),
    ('-1.1/4', Fraction(-5, 4)),
))
def test_fraction(s, value):
    assert utils.fraction(s) == value


@pytest.mark.parametrize("f, str", (
    (None, "None"),
    (3, "3"),
    (-3, "-3"),
    (3.14159, "3.142"),
    ((Fraction(4, 3), (-3, Fraction(-4, 3))), "(1.1/3, (-3, -1.1/3))"),
    ([Fraction(4, 3), (-3, Fraction(-4, 3))], "[1.1/3, (-3, -1.1/3)]"),
    (Fraction(1, 3), "1/3"),
    (Fraction(-1, 3), "-1/3"),
    (Fraction(4, 3), "1.1/3"),
    (Fraction(-4, 3), "-1.1/3"),
))
def test_f_to_str(f, str):
    assert utils.f_to_str(f) == str


@pytest.mark.parametrize("exp_in, exp_out", (
    ("a.b + 44", "a.b + 44"),
    ("a.b / 44", "a.b / 44"),
    ("5 / 44", "5 / 44"),
    ("5", "5"),
    ("5.67", "5.67"),
    ("5/44", "Fraction(5, 44)"),
    ("a.b + 5/44", "a.b + Fraction(5, 44)"),
    ("a.b + 2.5/44", "a.b + Fraction(93, 44)"),
))
def test_convert_exp(exp_in, exp_out):
    assert utils.convert_exp(exp_in) == exp_out

@pytest.mark.parametrize("s, value", (
    ('4', 4),
    ('1/4', Fraction(1, 4)),
    ('1.1/4', Fraction(5, 4)),
    ('-1.1/4', Fraction(-5, 4)),
    ('a', 1),
    ('-b', -2),
    ('!4', 2.0),
    ('-!4', -2.0),
))
def test_eval_num(s, constants, value):
    assert utils.eval_num(s, constants) == value


@pytest.mark.parametrize("s, value", (
    ('1.1/4', Fraction(5, 4)),
    ('-1.1/4', Fraction(-5, 4)),
    ('a', 1),
    ('b + 1.1/4 - a', Fraction(9, 4)),
    ('b + 2 - 2 * 2', 0),
    ('b + 2 - 2 / 2', 3),
    ('-b + 2', 0),
    ('1 / 4', Fraction(1, 4)),
    ('-1 / 4', Fraction(-1, 4)),
    ('2 * 2', 4),
    (123, 123),
))
def test_my_eval(s, constants, value):
    assert utils.my_eval(s, constants, "<test>") == value


@pytest.mark.parametrize("s, relaxed, value", (
    (('1.1/4', 'a'), False, (Fraction(5, 4), 1)),
    (('a + 1/4', '79'), False, (Fraction(5, 4), 79)),
    (('a + 1/4', 'a + b'), False, (Fraction(5, 4), 3)),
    (('a + b', 'a + 1/4 / 4'), False, (3, Fraction(17, 16))),
    ('a + 1/4', True, Fraction(5, 4)),
    (123, True, 123),
))
def test_eval_pair(s, constants, relaxed, value):
    assert utils.eval_pair(s, constants, "<test>", relaxed) == value


@pytest.mark.parametrize("s, value", (
    ('#123', '#123'),
    ('a', '#1'),
    ('white', 'white'),
))
def test_eval_color(s, colors, value):
    assert utils.eval_color(s, colors) == value


@pytest.mark.parametrize("value, ans", (
    (Mock(a=1), 1),
    ([Mock(a=1)], 1),
    ([Mock(a=1), Mock(a=1)], 1),
    ([Mock(a=1), Mock(a=2)], None),
))
def test_multi_getattr(value, ans):
    assert utils.multi_getattr(value, 'a') == ans
