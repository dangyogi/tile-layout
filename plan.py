# plan.py

import app
from utils import my_eval, eval_color, eval_tile
from tile import erase_tiles
from alignment import Alignment


class Plan:
    attrs = 'grout_gap,grout_color,alignment,layout'.split(',')

    def __init__(self, name, plan, wall_name):
        self.name = name
        for attr in self.attrs:
            value = plan[attr]
            if attr == 'alignment':
                value = Alignment(value)
            setattr(self, attr, value)
        self.wall_name = wall_name
        self.wall = app.Walls[wall_name]

    def __repr__(self):
        return f"<Plan: {self.name}>"

    def dump(self):
        return {attr: (getattr(self, attr) if attr != 'alignment' else getattr(self, attr).dump())
                for attr in self.attrs}

    def set_grout_color(self, color):
        self.grout_color = color
        self.display_grout_color()

    def display_grout_color(self):
        if app.Plan == self:
            app.canvas.itemconfig("grout", fill=eval_color(self.grout_color))

    def create(self):
        erase_tiles()
        self.display_grout_color()
        self.do_step(self.layout)

    def create_polygon(self, points, offset, color):
        r'''Does nothing if the points are not visible.

        Returns True if the points are visible, False otherwise.

        The `offset` is added to each point, and then the points are aligned before checking for
        visibility.
        '''
        aligned_points = self.alignment.align((x + offset[0], y + offset[1]) for x, y in points)
        if not self.wall.visible(aligned_points):
            return False
        item = app.canvas.create_my_polygon("tile placement", color, *aligned_points, tags=('tile',))
        app.canvas.tag_lower(item, "topmost")
        return True

    def place(self, offset, tile, trace=False):
        r'''Returns True if displayed, False if not visible.
        '''
        if trace:
            print(f"{self.name}.place({offset=}, {tile=})")
        return tile.place_at(offset, self)

    def sequence(self, offset, constants, *steps, trace=False):
        r'''Returns True if any step is displayed, False if nothing is visible.
        '''
        if trace:
            print(f"{self.name}.sequence({steps=})")
        visible = False
        for step in steps:
            if self.do_step(step, offset, constants, trace=trace):
                visible = True
        return visible

    def repeat(self, start, constants, step, increment, times=None, do_reverse=True, trace=False):
        r'''Repeat step `times` times (infinite in both directions if times is None).

        `increment` is added to the offset (starting at `start`) after each repetition.

        `do_reverse` is only for use by repeat itself.  Outside callers must let this default.

        Returns True if any repetition is visible, False if nothing is visible.
        '''
        if trace:
            print(f"{self.name}.repeat({step=})")
        visible = False
        x_inc, y_inc = increment
        ax_inc, ay_inc = self.alignment.align_pt(increment)
        x, y = offset = start
        check_visibility = False
        while times is None or times:
            if not check_visibility:
                ax, ay = self.alignment.align_pt((x, y))
                if     (ax_inc == 0 or ax_inc > 0 and ax >= 0 or ax_inc < 0 and ax < self.wall.max_x) \
                   and (ay_inc == 0 or ay_inc > 0 and ay >= 0 or ay_inc < 0 and ay < self.wall.max_y):
                    check_visibility = True
            if self.do_step(step, offset, constants, trace=trace):
                visible = True
            elif check_visibility:
                break
            x, y = offset = x + x_inc, y + y_inc
            if times is not None:
                times -= 1
        if times is None and do_reverse:
            if self.repeat((start[0] - x_inc, start[1] - y_inc), constants, step, (-x_inc, -y_inc),
                           do_reverse=False, trace=trace):
                return True
        return visible

    def do_step(self, step, offset=(0, 0), constants=None, trace=False):
        r'''Returns True if the step is visible, False otherwise.
        '''
        if trace:
            print(f"{self.name}.do_step({step=})")
        if constants is None:
            constants = {}
        constants['offset'] = offset
        constants['plan'] = self
        if step['type'] == 'place':
            return self.place(offset, eval_tile(step['tile'], constants), trace=trace)
        if step['type'] == 'sequence':
            return self.sequence(offset, constants, *step['steps'], trace=trace)
        if step['type'] == 'repeat':
            x, y = my_eval(step.get('start', (0, 0)), constants)
            x_off, y_off = offset
            return self.repeat((x_off + x, y_off + y), constants, step['step'],
                               my_eval(step['increment'], constants),
                               my_eval(step.get('times', None), constants),
                               trace=trace)

        # else it's a call to a layout
        new_step = app.Layouts[step['type']]
        def lookup(arg):
            if arg in step:
                if arg == 'tile' or arg.startswith('tile_'):
                    if trace:
                        print(f"{self.name}.lookup({arg}) in step -- type! -- value is {step[arg]}")
                    ans = eval_tile(step[arg], constants)
                else:
                    if trace:
                        print(f"{self.name}.lookup({arg}) in step -- value is {step[arg]}")
                    ans = my_eval(step[arg], constants)
            elif arg in constants:
                if trace:
                    print(f"{self.name}.lookup({arg}) in constants -- value is {constants[arg]}")
                ans = constants[arg]
            else:
                ans = None
            if trace:
                print(f"setting parameter {arg} to {ans}")
            return ans
        new_constants = {param: lookup(param)
                         for param in new_step.get('parameters', ())}
        new_constants['offset'] = offset
        new_constants['plan'] = self
        if 'constants' in new_step:
            def add_constants(constants):
                for name, value in constants.items():
                    if trace:
                        print(f"{self.name}: add_constants adding {name=}, {value=}")
                    if name == 'conditionals':
                        for conditional in value:
                            test = my_eval(conditional['test'], new_constants)
                            if trace:
                                print(f"{self.name}: add_constants got conditional {test=!r}, "
                                      f"{conditional=}")
                            add_constants(conditional[test])
                    elif name == 'tile':
                        new_constants[name] = eval_tile(value, new_constants)
                    else:
                        new_constants[name] = my_eval(value, new_constants)
            add_constants(new_step['constants'])
        return self.do_step(new_step, offset, new_constants, trace=trace)

