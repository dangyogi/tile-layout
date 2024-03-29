# utils.py

import re
import os
import os.path
from fractions import Fraction
from math import sqrt
from collections import ChainMap
from collections.abc import Mapping
import csv

from yaml import safe_load, dump


Code_dir = os.path.dirname(__file__)
Data_dir = Code_dir

#print(f"{__file__=!r}")
#print(f"{Code_dir=!r}")
#print(f"{Data_dir=!r}")


def fraction(s):
    r'''Format is optionally signed:

      <integer>
      <integer>.<numerator>/<denominator>
      <numerator>/<denominator>
    '''
    s = s.strip()
    if ' ' in s:
        raise SyntaxError("spaces not allowed in numbers")
    if '.' not in s:
        if '/' not in s:
            return int(s)
        return Fraction(s)
    i, b = s.split('.')
    rest = Fraction(b)
    if rest.denominator == 1:
        raise ValueError(f"invalid fraction: {s!r}")
    if i[0] == '-':
        return int(i) - rest
    return int(i) + rest


def f_to_str(f):
    if isinstance(f, (tuple, list)):
        segments = ['('] if isinstance(f, tuple) else ['[']
        for i, n in enumerate(f):
            if i:
                segments.append(f", {f_to_str(n)}")
            else:
                segments.append(f_to_str(n))
        segments.append(')' if isinstance(f, tuple) else ']')
        return ''.join(segments)
    if isinstance(f, Mapping):
        return {key: f_to_str(value) for key, value in f.items()}
    if isinstance(f, float):
        return f"{f:.3f}"
    if isinstance(f, str):
        return repr(f)
    if not isinstance(f, Fraction):
        return str(f)
    n, d = f.numerator, f.denominator  # this works for int's too!
    if d == 1:
        return str(n)
    if -1 < f < 1:
        return f"{n}/{d}"
    if f < 0:
        n = -n
        return f"-{n // d}.{n % d}/{d}"
    return f"{n // d}.{n % d}/{d}"


def format(x):
    if isinstance(x, Fraction):
        return f_to_str(x)
    if isinstance(x, (tuple, list)):
        return [format(y) for y in x]
    return x


Exp_cache = {}

def compile_exp(exp_source, location):
    exp_source = str(exp_source)
    if exp_source not in Exp_cache:
        Exp_cache[exp_source] = compile(convert_exp(exp_source), location, 'eval')
    return Exp_cache[exp_source]


def convert_exp(exp_source):
    r'''convert all fractions in exp_source to "Fraction(n, d)"
    '''
    segments = []
    start = 0
    for match in re.finditer(r'(?:([0-9]*)\.)?([0-9]+)/([0-9]+)', exp_source):
        segments.append(exp_source[start: match.start()])
        i, n, d = match.group(1, 2, 3)
        n = int(n)
        d = int(d)
        if i is None:
            i = 0
        else:
            i = int(i)
        segments.append(f"Fraction({i * d + n}, {d})")
        start = match.end()
    segments.append(exp_source[start:])
    return ''.join(segments)


def eval_num(s, constants):
    if not isinstance(s, str):
        return s
    s = s.strip()
    if s[0] == '-':
        negative = True
        s = s[1:].strip()
    else:
        negative = False
    if s[0] == '!':
        ans = sqrt(fraction(s[1:]))
    elif s[0].isdigit():
        try:
            ans = fraction(s)
        except ValueError:
            ans = s
    else:
        attrs = s.split('.')
        ans = constants[attrs[0]]
        for attr in attrs[1:]:
            ans = getattr(ans, attr)
        ans = eval_num(ans, {})
    if negative:
        return -ans
    return ans


def my_eval(s, constants, location):
    if isinstance(s, tuple):
        ans = tuple(my_eval(x, constants, location) for x in s)
    elif isinstance(s, list):
        ans = [my_eval(x, constants, location) for x in s]
        #print(f"my_eval({s},, {location}) list -> {ans}")
    elif not isinstance(s, str):
        ans = s
    else:
        temp_constants = ChainMap(dict(constants=constants), constants)
        ans = eval(compile_exp(s, location), globals(), temp_constants)
    #print(f"my_eval({s=}, {location=}) -> {ans}")
    return ans


def eval_pair(s, constants, location, relaxed=False):
    if relaxed and not isinstance(s, (tuple, list)):
        return my_eval(s, constants, location)
    assert isinstance(s, (tuple, list)) and len(s) == 2, \
           f"eval_pair expected list of 2 exps, got {s!r}"
    return tuple(my_eval(x, constants, location) for x in s)


def eval_color(s, colors=None):
    if colors is None:
        colors = app.Colors
    if s is None:
        return None
    if s[0] == '#': return s
    try:
        return colors[s.lower()]
    except KeyError:
        #print("eval_color: don't know", s)
        return s


def eval_tile(s, constants):
    if s is None:
        return None
    if isinstance(s, (tuple, list)):
        return [eval_tile(x, constants) for x in s]
    if '.' in s:
        attrs = s.split('.')
        temp_constants = ChainMap({}, constants)
        temp_s = s
        if attrs[0] not in constants:
            temp_constants['_placeholder_'] = app.Tiles[attrs[0]]
            temp_s = '_placeholder_.' + '.'.join(attrs[1:])
        #print(f"eval_tile({s}) -> {temp_s=}")
        ans = my_eval(temp_s, temp_constants, f"eval_tile({s})")
    elif s in constants:
        ans = constants[s]
        #print(f"eval_tile({s}): in constants {ans=}")
    else:
        ans = s
        #print(f"eval_tile({s}): not in constants {ans=}")
    if isinstance(ans, str):
        ans = app.Tiles[ans]
    return ans


def multi_getattr(value, attr):
    if not isinstance(value, (tuple, list)):
        return getattr(value, attr)
    ans = getattr(value[0], attr)
    if any(getattr(v, attr) != ans for v in value):
        return None
    return ans


def pick(value, constants, selector=None, reverse=False):
    r'''Picks a value out of `value` list round robin based on 'index' in `constants`.

    If 'index_by_counter' is in `constants`, uses app.Counters[constants['index_by_counter'], selector].

    `reverse` causes Counter to be initially set to len(value) - 1 and be decremented each time called.
    '''
    if not isinstance(value, (tuple, list)):
        value = [value]
    if 'index_by_counter' in constants:
        key = constants['index_by_counter'], selector
        if reverse and key not in app.Counters:
            app.Counters[key] = len(value) - 1
        ans = value[app.Counters[key] % len(value)]
        print(f"pick({value}, , {selector=}, {reverse=}) got index_by_counter {key}, index {app.Counters[key]}, ans {ans}")
        if reverse:
            app.Counters[key] -= 1
        else:
            app.Counters[key] += 1
        return ans
    return value[constants.get('index', 0) % len(value)]


def unpick(constants, selector=None, reverse=False):
    r'''Reverses a pick if it was 'index_by_counter'.
    '''
    if 'index_by_counter' in constants:
        key = constants['index_by_counter'], selector
        if reverse:
            app.Counters[key] += 1
        else:
            app.Counters[key] -= 1
        print(f"unpick(, {selector=}, {reverse=}) got index_by_counter {key}, index {app.Counters[key]}")


def read_yaml(filename):
    with open(os.path.join(Data_dir, filename), "r") as yaml_file:
        return safe_load(yaml_file)


def write_yaml(data, filename):
    with open(os.path.join(Data_dir, filename), "w") as yaml_file:
        print("#", filename, file=yaml_file)
        print(file=yaml_file)
        dump(data, yaml_file, explicit_start=True, width=90, indent=4)


def backup_file(filename, backup_suffix='.bck'):
    full_path = os.path.join(Data_dir, filename)
    os.replace(full_path, full_path + backup_suffix)


def read_csv(filename, ignore_header=True):
    with open(os.path.join(Data_dir, filename), "r") as csv_file:
        lines = list(csv.reader(csv_file))
        if ignore_header:
            return lines[1:]
        return lines

import app



if __name__ == "__main__":
    import sys
    from pprint import pp

    if sys.argv[1] == 'read_yaml':
        filename = sys.argv[2]
        print("filename", filename)
        pp(read_yaml(filename))
    elif sys.argv[1] == 'read_csv':
        filename = sys.argv[2]
        print("filename", filename)
        for line in read_csv(filename):
            print(line)
    elif sys.argv[1] == 'eval_num':
        print(f_to_str(eval_num(sys.argv[2], dict(a=1, b=2))))
    elif sys.argv[1] == 'my_eval':
        print(f_to_str(my_eval(sys.argv[2], dict(a=1, b=2), f"<test>")))
    elif sys.argv[1] == 'eval_pair':
        print(eval_pair(sys.argv[2], dict(a=1, b=2)))
    elif sys.argv[1] == 'help':
        print("Commands:")
        print("  eval_pair")
        print("  eval_num")
        print("  help")
        print("  my_eval")
        print("  read_csv")
        print("  read_yaml")
    else:
        print("invalid command", sys.argv[1])

