# layouts.py

from utils import read_yaml


def read_layouts(filename='layouts.yaml'):
    return read_yaml(filename)



if __name__ == "__main__":
    from pprint import pp

    pp(read_layouts())
