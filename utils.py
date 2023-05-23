# utils.py

import re
import os.path
from fractions import Fraction
from math import sqrt
import csv

from yaml import safe_load


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
    if isinstance(f, tuple):
        segments = ['(']
        for i, n in enumerate(f):
            if i:
                segments.append(f", {f_to_str(n)}")
            else:
                segments.append(f_to_str(n))
        segments.append(')')
        return ''.join(segments)
    if isinstance(f, float):
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


def eval_term(s, constants, trace=False):
    ans = 1
    op = None
    start = 0

    def eval_op(op, a, b):
        if op == ' * ':
            return a * b
        if op == ' / ':
            if trace:
                print("/ got", a, b)
            if isinstance(a, int) and isinstance(b, int):
                ans = Fraction(a, b)
                if ans.denominator == 1:
                    ans = ans.numerator
                if trace:
                    print("creating Fraction", ans)
            else:
                ans = a / b
                if trace:
                    print("ans", ans)
            return ans
        return b

    for match in re.finditer(r' \* | / ', s):
        #print(f"got op={match.group()!r}, {start=}, {match.start()=}, {match.end()}")
        a = eval_num(s[start:match.start()], constants)
        ans = eval_op(op, ans, a)
        op = match.group()
        start = match.end()
    a = eval_num(s[start:], constants)
    return eval_op(op, ans, a)


def my_eval(s, constants, trace=False):
    if not isinstance(s, str):
        return s
    ans = 0
    op = None
    start = 0
    for match in re.finditer(r'[-+]', s):
        #print(f"got op={match.group()!r}, {start=}, {match.start()=}, {match.end()}")
        a = eval_term(s[start:match.start()], constants, trace=trace)
        if trace:
            print(f"my_eval: {ans=}, {op=}, {a=}")
        if op == '+': ans += a
        elif op == '-': ans -= a
        else: ans = a
        op = match.group()
        start = match.end()
    a = eval_term(s[start:], constants, trace=trace)
    if trace:
        print(f"my_eval: final {ans=}, {op=}, {a=}")
    if op == '+': return ans + a
    if op == '-': return ans - a
    return a


def eval_pair(s, constants, relaxed=False):
    if relaxed and not isinstance(s, (tuple, list)):
        return my_eval(s, constants)
    assert isinstance(s, (tuple, list)) and len(s) == 2, \
           f"eval_pair expected list of 2 exps, got {s!r}"
    return tuple(my_eval(x, constants) for x in s)


def eval_color(s, colors=None):
    if colors is None:
        colors = app.Colors
    if s[0] == '#': return s
    try:
        return colors[s.lower()]
    except KeyError:
        #print("eval_color: don't know", s)
        return s


def eval_tile(s, constants):
    if '.' in s:
        attrs = s.split('.')
        ans = constants[attrs[0]]
        for attr in attrs[1:]:
            ans = getattr(ans, attr)
    elif s in constants:
        ans = constants[s]
    else:
        ans = s
    if isinstance(ans, str):
        ans = app.Tiles[ans]
    return ans


def read_yaml(filename):
    with open(os.path.join(Data_dir, filename), "r") as yaml_file:
        return safe_load(yaml_file)


def write_yaml(data, filename):
    with open(os.path.join(Data_dir, filename), "w") as yaml_file:
        print("#", filename, file=yaml_file)
        print(file=yaml_file)
        dump(data, yaml_file, explicit_start=True, width=90, indent=4)


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
    elif sys.argv[1] == 'eval_term':
        print(f_to_str(eval_term(sys.argv[2], dict(a=1, b=2))))
    elif sys.argv[1] == 'my_eval':
        print(f_to_str(my_eval(sys.argv[2], dict(a=1, b=2))))
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

