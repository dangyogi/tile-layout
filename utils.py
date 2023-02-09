# utils.py

import re
import os.path
from fractions import Fraction
import csv

from yaml import safe_load


Code_dir = os.path.dirname(__file__)
Data_dir = Code_dir

#print(f"{__file__=!r}")
#print(f"{Code_dir=!r}")
#print(f"{Data_dir=!r}")


def fraction(s):
    s = s.strip()
    if '.' not in s:
        if '/' not in s:
            return int(s)
        return Fraction(s)
    i, b = s.split('.')
    rest = Fraction(b)
    if rest.denominator == 1:
        raise ValueError(f"invalid fraction: {s!r}")
    return int(i) + rest


def f_to_str(f):
    n, d = f.numerator, f.denominator
    if d == 1:
        return str(n)
    if -1 < f < 1:
        return f"{n}/{d}"
    if f < 0:
        n = -n
        return f"-{n // d}.{n % d}/{d}"
    return f"{n // d}.{n % d}/{d}"


def eval_num(s, constants):
    s = s.strip()
    if s[0].isdigit():
        return fraction(s)
    return constants[s]


def my_eval(s, constants):
    ans = 0
    op = None
    start = 0
    for match in re.finditer(r'[-+]', s):
        #print(f"got op={match.group()!r}, {start=}, {match.start()=}, {match.end()}")
        a = eval_num(s[start:match.start()], constants)
        if op == '+': ans += a
        elif op == '-': ans -= a
        else: ans = a
        op = match.group()
        start = match.end()
    a = eval_num(s[start:], constants)
    if op == '+': return ans + a
    if op == '-': return ans - a
    return a


def eval_pair(s, constants):
    a, b = s.split(',')
    return my_eval(a, constants), my_eval(b, constants)


def eval_color(s, colors):
    if s[0] == '#': return s
    try:
        return colors[s.lower()]
    except KeyError:
        #print("eval_color: don't know", s)
        return s


def read_yaml(filename):
    with open(os.path.join(Data_dir, filename), "r") as yaml_file:
        return safe_load(yaml_file)


def read_csv(filename, ignore_header=True):
    with open(os.path.join(Data_dir, filename), "r") as csv_file:
        lines = list(csv.reader(csv_file))
        if ignore_header:
            return lines[1:]
        return lines


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
        print(my_eval(sys.argv[2], dict(a=1, b=2)))
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

