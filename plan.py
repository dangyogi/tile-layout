# plan.py

from collections import ChainMap
from itertools import count

import app
from utils import my_eval, eval_pair, eval_color, eval_tile, format, f_to_str
from tile import erase_tiles
from alignment import Alignment
from place_trace import pt_init, place


class Plan:
    attrs = 'grout_gap,grout_color,alignment,layout'.split(',')

    def __init__(self, name, plan, wall_name, constants):
        self.name = name
        for attr in self.attrs:
            value = plan[attr]
            if attr == 'alignment':
                value = Alignment(value, constants)
            if attr == 'grout_gap':
                setattr(self, attr, my_eval(value, constants, f"<Plan({name}): {attr}>"))
            else:
                setattr(self, attr, value)
        self.wall_name = wall_name
        self.wall = app.Walls[wall_name]
        if wall_name == "Master Back" and name == 'star_+':
            print(f"Plan({wall_name}, {name}): angle={self.alignment.angle}, "
                  f"x_offset={f_to_str(self.alignment.x_offset)}, "
                  f"y_offset={f_to_str(self.alignment.y_offset)}")

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
        pt_init()
        self.do_step(f"Plan({self.name})", self.layout,
                     #dict(plan=self, offset=(-self.wall.diagonal, -self.wall.diagonal)))
                     dict(plan=self, offset=(0, 0)))

    def get_inc_xy(self, steps, constants):
        temp_constants = ChainMap(dict(plan=self, offset=(0, 0), skip=True), constants)
        if not isinstance(steps, (tuple, list)):
            steps = [steps]
        inc_x = inc_y = None
        x_dead = y_dead = False
        for step in steps:
            ans_constants = temp_constants.new_child()
            assert self.do_step("get_inc_xy", step, ans_constants), \
                   f"get_inc_xy: {step=} not visible"
            if inc_x is None and not x_dead:
                inc_x = ans_constants['inc_x']
            elif inc_x != ans_constants['inc_x']:
                inc_x = None
                x_dead = True
            if inc_y is None and not y_dead:
                inc_y = ans_constants['inc_y']
            elif inc_y != ans_constants['inc_y']:
                inc_x = None
                y_dead = True
        print(f"get_inc_xy: {steps=}")
        print(f"  {constants=}")
        print(f"  inc_x={f_to_str(inc_x)}, inc_y={f_to_str(inc_y)}")
        return inc_x, inc_y

    def align(self, points, offset):
        r'''Returns aligned points after applying offset.

        If the aligned points are not visible, returns None.
        '''
        aligned_points = self.alignment.align((x + offset[0], y + offset[1])
                                              for x, y in points)
        if self.wall.visible(aligned_points):
            return aligned_points
        return None

    def create_polygon(self, points, offset, color, skip):
        r'''Does nothing if the points are not visible.

        Returns True if the points are visible, False otherwise.

        The `offset` is added to each point, and then the points are aligned
        before checking for visibility.
        '''
        aligned_points = self.align(points, offset)
        if aligned_points is None:
            return False
        if not skip:
            item = app.canvas.create_my_polygon("plan", color, *aligned_points,
                                                tags=('tile',))
            app.canvas.tag_lower(item, "topmost")
        return True

    def create_image(self, image, sw_offset, pos):
        item = app.canvas.create_my_image("plan", image, sw_offset, pos, tags=('tile',))
        app.canvas.tag_lower(item, "topmost")

    def place(self, step_name, tile, angle, constants, trace=False):
        r'''Returns True if displayed, False if not visible.

        If visible, updates `inc_x` and `inc_y` in `constants` (including grout_gap).
        '''
        if trace:
            print(f"{step_name}.place(tile={tile}, angle={angle}, "
                  f"offset={constants['offset']})")
        the_tile = pick(tile, constants)
        visible = the_tile.place_at(constants['offset'], pick(angle, constants), self,
                                    constants.get('skip', False))
        place(constants['offset'], visible)
        if visible:
            constants['inc_x'] = the_tile.skip_x + self.grout_gap
            constants['inc_y'] = the_tile.skip_y + self.grout_gap
            return True
        return False

    def sequence(self, step_name, constants, *steps, trace=False):
        r'''Returns True if any step is displayed, False if nothing is visible.

        If visible, returns the greatest inc_x, inc_y in constants.

        The sequence executes with it's own constants that are discarded when it's done.
        Additionally, each step executes with it's own disposable constants.

        Values can be copied from an individual step's constants to the sequence's
        constants by placing 'save' on that step with a dict of sequence keys and
        expressions.

        Values can be copied from the sequence's constants to an individual step's
        constants by placing 'use' on that step with a dict of step keys and expressions.

        Thus, 'use' processing is done prior to running the step, while 'save' processing
        is done afterwards.

        The initial offset is stored as constants in 'initial_x', 'initial_y'.  By default,
        these are used for the offset of each step.

        To override this default, each step may specify an 'offset' that is added to
        'initial_x', 'initial_y', or specify the offset directly as 'offset_x', 'offset_y'.
        '''
        if trace:
            print(f"{step_name}.sequence({steps=})")
        visible = False
        inc_x = inc_y = None
        initial_x, initial_y = constants['offset']
        my_constants = ChainMap({}, constants)
        my_constants['initial_x'] = initial_x
        my_constants['initial_y'] = initial_y
        for i, step in enumerate(steps, 1):
            print(f"{step_name}.sequence: step {i}, {step=}, {constants=}")
            step = pick(step, constants)
            step_constants = my_constants.new_child()
            step_constants['offset_x'] = step_constants['initial_x']
            step_constants['offset_y'] = step_constants['initial_y']
            if 'use' in step:
                for key, value in step['use'].items():
                    step_constants[key] = \
                      my_eval(value, step_constants,
                              f"<{step_name}.sequence: use {key}>")
            if 'offset' in step:
                x, y = my_eval(step['offset'], step_constants,
                               f"<{step_name}.sequence: offset>")
                step_constants['offset'] = \
                  step_constants['initial_x'] + x, step_constants['initial_y'] + y
            else:
                step_constants['offset'] = \
                  step_constants['offset_x'], step_constants['offset_y']
            if self.do_step(f"{step_name}.sequence, step {i}", step, step_constants,
                            trace=trace):
                if 'save' in step:
                    print(f"{step_name}.sequence: save {f_to_str(step_constants)}")
                    for key, value in step['save'].items():
                        my_constants[key] = \
                          my_eval(value, step_constants,
                                  f"{step_name}.sequence: save {key}>")
                        print(f"{step_name}.sequence save {key} set to "
                              f"{f_to_str(my_constants[key])}")
                if inc_x is None or step_constants['inc_x'] > inc_x:
                    inc_x = step_constants['inc_x']
                if inc_y is None or step_constants['inc_y'] > inc_y:
                    inc_y = step_constants['inc_y']
                visible = True
        if visible:
            constants['inc_x'] = inc_x
            constants['inc_y'] = inc_y
        return visible

    def repeat(self, step_name, constants, step, increment, times,
               step_width_limit, step_height_limit, index_start, trace=False):
        r'''Repeat step `times` times (infinite in both directions if times is None).

        `increment` is added to the offset after each repetition.

        Returns True if any repetition is visible, False if nothing is visible.

        If visible, returns the greatest inc_x, inc_y in constants.
        '''
        if trace or True:
            print(f"{step_name}.repeat({step=}, "
                  f"increment={f_to_str(increment)}, {times=}, "
                  f"{step_width_limit=}, {step_height_limit=}, {index_start=})")
        if True:
            unaligned_boundary = self.alignment.unalign(self.wall.boundary)
            print(f"{step_name}.repeat: "
                  f"unaligned_boundary={f_to_str(unaligned_boundary)}")
            min_x = min(p[0] for p in unaligned_boundary) - 2 * step_width_limit
            max_x = max(p[0] for p in unaligned_boundary)
            min_y = min(p[1] for p in unaligned_boundary) - 2 * step_width_limit
            max_y = max(p[1] for p in unaligned_boundary)
        else:
            min_x = min_y = -self.wall.diagonal - 2 * step_width_limit
            max_x = max_y = self.wall.diagonal + step_width_limit
        print(f"{step_name}.repeat: "
              f"min_x={min_x:.2f}, max_x={max_x:.2f}, "
              f"min_y={min_y:.2f}, max_y={max_y:.2f}")
        visible = False
        inc_x = inc_y = None
        x_inc, y_inc = increment
        x, y = offset = starting_offset = constants['offset']
        print(f"{step_name}.repeat offset={f_to_str(offset)}, {times=}, "
              f"x_inc={f_to_str(x_inc)}, y_inc={f_to_str(y_inc)}")
        print(f"  min_x={f_to_str(min_x)}, max_x={f_to_str(max_x)}, "
              f"min_y={f_to_str(min_y)}, max_y={f_to_str(max_y)}")
        for index in (range(times) if times is not None else count(0)):
            #print(f"{step_name}.repeat {index=}, offset={f_to_str(offset)}")
            constants['offset'] = offset
            constants['index'] = index + index_start
            step_visible = self.do_step(f"{step_name}.repeat", pick(step, constants),
                                        constants, trace=trace)
            if step_visible:
                step_inc_x = constants['inc_x'] + index * x_inc
                step_inc_y = constants['inc_y'] + index * y_inc
                if inc_x is None or step_inc_x > inc_x:
                    inc_x = step_inc_x
                if inc_y is None or step_inc_y > inc_y:
                    inc_y = step_inc_y
                visible = True
            if times is None:
                keep_going = step_visible or \
                             x_inc > 0 and x <= max_x or \
                             x_inc < 0 and x >= min_x or \
                             y_inc > 0 and y <= max_y or \
                             y_inc < 0 and y >= min_y
                if not keep_going:
                    break
            x, y = offset = x + x_inc, y + y_inc
        if times is None:
            # go backwards
            x_inc, y_inc = -x_inc, -y_inc
            x, y = offset = starting_offset[0] + x_inc, starting_offset[1] + y_inc
            for index in count(-1, -1):
                #print(f"{step_name}.repeat {index=}, offset={f_to_str(offset)}")
                constants['offset'] = offset
                constants['index'] = index + index_start
                step_visible = self.do_step(f"{step_name}.repeat backwards",
                                            pick(step, constants), constants, trace=trace)
                if step_visible:
                    step_inc_x = constants['inc_x'] + index * x_inc
                    step_inc_y = constants['inc_y'] + index * y_inc
                    if inc_x is None or step_inc_x > inc_x:
                        inc_x = step_inc_x
                    if inc_y is None or step_inc_y > inc_y:
                        inc_y = step_inc_y
                    visible = True
                keep_going = step_visible or \
                             x_inc > 0 and x <= max_x or \
                             x_inc < 0 and x >= min_x or \
                             y_inc > 0 and y <= max_y or \
                             y_inc < 0 and y >= min_y
                if not keep_going:
                    break
                x, y = offset = x + x_inc, y + y_inc
        if visible:
            constants['inc_x'] = inc_x
            constants['inc_y'] = inc_y
        print(f"{step_name}.repeat {visible=}, inc_x={f_to_str(inc_x)}, "
              f"inc_y={f_to_str(inc_y)}")
        return visible

    def section(self, step_name, alignment, grout_gap, pos, size, layout, constants,
                trace=False):
        pass

    def do_step(self, step_name, step, constants, trace=False):
        r'''Returns True if the step is visible, False otherwise.
        '''
        if trace or True:
            print(f"{self.name}.do_step({step_name=}, {step=})")
        if 'inc_x' in constants:
            constants['inc_x'] = None
        if 'inc_y' in constants:
            constants['inc_y'] = None
        if step['type'] == 'place':
            return self.place(step_name, eval_tile(step['tile'], constants),
                              my_eval(step.get('angle', 0), constants,
                                      f"<{step_name}.do_step: place angle>"),
                              constants, trace=trace)
        if step['type'] == 'sequence':
            return self.sequence(step_name, constants, *step['steps'], trace=trace)
        if step['type'] == 'repeat':
            x, y = my_eval(step.get('start', (0, 0)), constants,
                           f"<{step_name}.do_step: repeat start>")
            x_off, y_off = constants['offset']
            print(f"do_step: repeat in {step_name} "
                  f"x={f_to_str(x)}, y={f_to_str(y)}, "
                  f"x_off={f_to_str(x_off)}, y_off={f_to_str(y_off)}")
            constants['offset'] = x_off + x, y_off + y
            return self.repeat(step_name, constants,
                               my_eval(step['step'], constants,
                                 f"{step_name} repeat step"),
                               my_eval(step['increment'], constants,
                                 f"<{step_name}.do_step: repeat increment>"),
                               my_eval(step.get('times', None), constants,
                                 f"<{step_name}.do_step: repeat times>"),
                               my_eval(step.get('step_width_limit', 24), constants,
                                 f"<{step_name}.do_step: repeat "
                                 "step_width_limit>"),
                               my_eval(step.get('step_height_limit', 24), constants,
                                 f"<{step_name}.do_step: repeat step_height_limit>"),
                               my_eval(step.get('index_start', 0), constants,
                                 f"<{step_name}.do_step: repeat index_start>"),
                               trace=trace)

        # else it's a call to a layout
        new_step = app.Layouts[step['type']]
        def lookup(param, defaults):
            if param in step:
                if param in ('tile', 'tiles') or param.startswith('tile_'):
                    if trace:
                        print(f"{step_name}.lookup({param}) in step -- tile! "
                              f"-- value is {step[param]}")
                    ans = eval_tile(step[param], constants)
                    print(f"{step['type']}: setting {param=}, {step[param]=} to {ans}")
                else:
                    if trace:
                        print(f"{step_name}.lookup({param}) in step -- "
                              f"value is {step[param]}")
                    ans = my_eval(step[param], constants,
                                  f"<{step_name}.do_step: layout {step['type']} "
                                  f"{param}>")
            #elif param in constants:
            #    if trace:
            #        print(f"{step_name}.lookup({param}) in constants "
            #              f"-- value is {constants[param]}")
            #    ans = constants[param]
            elif param in defaults:
                ans = my_eval(defaults[param], new_constants,
                              f"<{step_name}.do_step: layout {step['type']} "
                              f"defaults {param}>")
            else:
                ans = None
            if trace:
                print(f"{step['type']}: setting parameter {param} to {ans}")
            return ans
        if 'defaults' in new_step:
            defaults = new_step['defaults']
        else:
            defaults = {}
        print(f"{step['type']} {defaults=}")
        new_constants = ChainMap({}, constants)
        for param in new_step.get('parameters', ()):
            new_constants[param] = lookup(param, defaults)
        #new_constants['plan'] = self
        #new_constants['offset'] = constants['offset']
        if 'constants' in new_step:
            def add_constants(constants):
                for name, value in constants.items():
                    if trace or True:
                        print(f"{step['type']}: add_constants adding {name=}, {value=}")
                    if name == 'conditionals':
                        for conditional in value:
                            test = my_eval(conditional['test'], new_constants,
                                           f"<{step_name}.do_step: "
                                           f"layout {step['type']} conditionals test>")
                            if trace:
                                print(f"{step['type']}: add_constants got "
                                      f"conditional {test=!r}, {conditional=}")
                            if test in conditional:
                                add_constants(conditional[test])
                            else:
                                add_constants(conditional['else'])
                    elif name in ('tile', 'tiles') or name.startswith('tile_'):
                        new_constants[name] = eval_tile(value, new_constants)
                    else:
                        new_constants[name] = my_eval(value, new_constants,
                                                f"<{step_name}.do_step: "
                                                f"layout {step['type']} {name}>")
            add_constants(new_step['constants'])
        print(f"{step['type']}: {new_constants=}")
        visible = self.do_step(step['type'], new_step, new_constants, trace=trace)
        if visible:
            constants['inc_x'] = new_constants['inc_x']
            constants['inc_y'] = new_constants['inc_y']
        return visible


def pick(value, constants):
    if not isinstance(value, (tuple, list)):
        value = [value]
    return value[constants.get('index', 0) % len(value)]


def get(value, attr=None):
    if not isinstance(value, (tuple, list)):
        value = [value]
    ans = None
    for x in value:
        if attr is None:
            xv = x
        else:
            xv = getattr(x, attr)
        if ans is None:
            ans = xv
        elif ans != xv:
            return None
    return ans

