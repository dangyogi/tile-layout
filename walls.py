# walls.py

from utils import read_yaml, my_eval, eval_pair, eval_color


def read_walls(colors, filename='walls.yaml'):
    def parse(specs):
        constants = {}
        if 'constants' in specs:
            for name, exp in specs['constants'].items():
                constants[name] = my_eval(exp, constants)
            del specs['constants']
        ans = [eval_pair(specs['grout'], constants)]
        del specs['grout']
        constants['bg_width'], constants['bg_height'] = ans[0]
        for name, panel in specs.items():
            #print(f"got {name=} {panel=}")
            ans.append((eval_pair(panel['pos'], constants),
                        eval_pair(panel['size'], constants, relaxed=True),
                        eval_color(panel['color'], colors)))
        return ans
        #return [(eval_pair(panel['pos'], constants),
        #         eval_pair(panel['size'], constants),
        #         eval_color(panel['color'], colors))
        #        for panel in specs.values()]
    return {name: parse(specs)
            for name, specs in read_yaml(filename).items()}



if __name__ == "__main__":
    from pprint import pp

    pp(read_walls(dict(cabinet='#123')))
