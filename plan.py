# plan.py

from collections import ChainMap

import app
from utils import my_eval, eval_color, eval_tile, format
from tile import erase_tiles
from alignment import Alignment


class Plan:
    attrs = 'grout_gap,grout_color,alignment,layout'.split(',')

    def __init__(self, name, plan, wall_name, constants):
        self.name = name
        for attr in self.attrs:
            value = plan[attr]
            if attr == 'alignment':
                value = Alignment(value, constants)
            if attr == 'grout_gap':
                setattr(self, attr, my_eval(value, constants))
            else:
                setattr(self, attr, value)
        self.wall_name = wall_name
        self.wall = app.Walls[wall_name]

    def __repr__(self):
        return f"<Plan: {self.name}>"

    def dump(self):
        return {attr: (format(getattr(self, attr)) 
                       if attr != 'alignment'
                       else getattr(self, attr).dump())
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

    def align(self, points, offset):
        r'''Returns aligned points after applying offset.

        If the aligned points are not visible, returns None.
        '''
        aligned_points = self.alignment.align((x + offset[0], y + offset[1]) for x, y in points)
        if self.wall.visible(aligned_points):
            return aligned_points
        return None

    def create_polygon(self, points, offset, color):
        r'''Does nothing if the points are not visible.

        Returns True if the points are visible, False otherwise.

        The `offset` is added to each point, and then the points are aligned before checking for
        visibility.
        '''
        aligned_points = self.align(points, offset)
        if aligned_points is None:
            return False
        item = app.canvas.create_my_polygon("plan", color, *aligned_points, tags=('tile',))
        app.canvas.tag_lower(item, "topmost")
        return True

    def create_image(self, image, sw_offset, pos):
        item = app.canvas.create_my_image("plan", image, sw_offset, pos, tags=('tile',))
        app.canvas.tag_lower(item, "topmost")

    def place(self, tile, angle, constants, trace=False):
        r'''Returns True if displayed, False if not visible.

        If visible, updates `next_x` and `next_y` in `constants` (including grout_gap).
        '''
        if trace:
            print(f"{self.name}.place({tile=}, {angle=}, offset={constants['offset']})")
        if tile.place_at(constants['offset'], angle, self):
            constants['next_x'] = tile.skip_x + self.grout_gap
            constants['next_y'] = tile.skip_y + self.grout_gap
            return True
        return False

    def sequence(self, constants, *steps, trace=False):
        r'''Returns True if any step is displayed, False if nothing is visible.

        If visible, returns the greatest next_x, next_y in constants.
        '''
        if trace:
            print(f"{self.name}.sequence({steps=})")
        visible = False
        next_x = next_y = -1000
        start_x, start_y = constants['offset']
        my_constants = ChainMap({}, constants)
        for step in steps:
            step_constants = my_constants.new_child()
            if 'use' in step:
                for key, value in step['use'].items():
                    step_constants[key] = my_eval(value, step_constants)
            if 'offset' in step:
                x, y = my_eval(step['offset'], step_constants)
                step_constants['offset'] = start_x + x, start_y + y
            else:
                step_constants['offset'] = start_x, start_y
            if self.do_step(step, step_constants, trace=trace):
                if 'save' in step:
                    for key, value in step['save'].items():
                        my_constants[key] = my_eval(value, step_constants)
                if step_constants['next_x'] > next_x:
                    next_x = step_constants['next_x']
                if step_constants['next_y'] > next_y:
                    next_y = step_constants['next_y']
                visible = True
        if visible:
            constants['next_x'] = next_x
            constants['next_y'] = next_y
        return visible

    def repeat(self, constants, step, increment, times=None, do_reverse=True, trace=False):
        r'''Repeat step `times` times (infinite in both directions if times is None).

        `increment` is added to the offset after each repetition.

        `do_reverse` is only for use by repeat itself.  Outside callers must let this default.

        Returns True if any repetition is visible, False if nothing is visible.

        If visible, returns the greatest next_x, next_y in constants.
        '''
        if trace:
            print(f"{self.name}.repeat({step=})")
        visible = False
        next_x = next_y = -1000
        x_inc, y_inc = increment
        ax_inc, ay_inc = self.alignment.rotate(increment)
        x, y = offset = start = constants['offset']
        check_visibility = False
        while times is None or times:
            if not check_visibility:
                ax, ay = self.alignment.align_pt((x, y))
                if     (   ax_inc == 0
                        or ax_inc > 0 and ax >= 0 
                        or ax_inc < 0 and ax < self.wall.max_x) \
                   and (   ay_inc == 0
                        or ay_inc > 0 and ay >= 0
                        or ay_inc < 0 and ay < self.wall.max_y):
                    check_visibility = True
            constants['offset'] = offset
            if self.do_step(step, constants, trace=trace):
                if constants['next_x'] > next_x:
                    next_x = constants['next_x']
                if constants['next_y'] > next_y:
                    next_y = constants['next_y']
                visible = True
            elif check_visibility:
                break
            x, y = offset = x + x_inc, y + y_inc
            if times is not None:
                times -= 1
        if times is None and do_reverse:
            constants['offset'] = start[0] - x_inc, start[1] - y_inc
            if self.repeat(constants, step, (-x_inc, -y_inc), do_reverse=False, trace=trace):
                if constants['next_x'] > next_x:
                    next_x = constants['next_x']
                if constants['next_y'] > next_y:
                    next_y = constants['next_y']
                visible = True
        if visible:
            constants['next_x'] = next_x
            constants['next_y'] = next_y
        return visible

    def do_step(self, step, constants=None, trace=False):
        r'''Returns True if the step is visible, False otherwise.
        '''
        if trace:
            print(f"{self.name}.do_step({step=})")
        if constants is None:
            constants = {}
            constants['plan'] = self
            constants['offset'] = 0, 0
        if 'next_x' in constants:
            del constants['next_x']
        if 'next_y' in constants:
            del constants['next_y']
        if step['type'] == 'place':
            return self.place(eval_tile(step['tile'], constants),
                              (my_eval(step['angle'], constants) if 'angle' in step else 0),
                              constants, trace=trace)
        if step['type'] == 'sequence':
            return self.sequence(constants, *step['steps'], trace=trace)
        if step['type'] == 'repeat':
            x, y = my_eval(step.get('start', (0, 0)), constants)
            x_off, y_off = constants['offset']
            constants['offset'] = x_off + x, y_off + y
            return self.repeat(constants, step['step'],
                               my_eval(step['increment'], constants),
                               my_eval(step.get('times', None), constants),
                               trace=trace)

        # else it's a call to a layout
        new_step = app.Layouts[step['type']]
        def lookup(arg):
            if arg in step:
                if arg == 'tile' or arg.startswith('tile_'):
                    if trace:
                        print(f"{self.name}.lookup({arg}) in step -- tile! "
                              f"-- value is {step[arg]}")
                    ans = eval_tile(step[arg], constants)
                else:
                    if trace:
                        print(f"{self.name}.lookup({arg}) in step -- value is {step[arg]}")
                    ans = my_eval(step[arg], constants)
            elif arg in constants:
                if trace:
                    print(f"{self.name}.lookup({arg}) in constants "
                          f"-- value is {constants[arg]}")
                ans = constants[arg]
            else:
                ans = None
            if trace:
                print(f"setting parameter {arg} to {ans}")
            return ans
        new_constants = {param: lookup(param)
                         for param in new_step.get('parameters', ())}
        new_constants['plan'] = self
        new_constants['offset'] = constants['offset']
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
        visible = self.do_step(new_step, new_constants, trace=trace)
        if visible:
            constants['next_x'] = new_constants['next_x']
            constants['next_y'] = new_constants['next_y']
        return visible

