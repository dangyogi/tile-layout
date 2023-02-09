# colors.py

from utils import read_csv


def read_colors(filename='colors.csv'):
    return dict(read_csv(filename))



if __name__ == "__main__":
    from pprint import pp

    pp(read_colors())
