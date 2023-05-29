# plan.py

from collections import ChainMap
from itertools import count

import app
from utils import my_eval, eval_pair, eval_color, eval_tile, format, f_to_str
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
                setattr(self, attr, my_eval(value, constants, f"<Plan({name}): {attr}>"))
            else:
                setattr(self, attr, value)
        self.wall_name = wall_name
        self.wall = app.Walls[wall_name]
        if wall_name == "Master Back" and name == 'star_+':
            print(f"Plan({wall_name}, {name}): angle={self.alignment.angle}, "
                  f"x_offset={f_to_str(self.alignment.x_offset)}, "
                  f"y_offset={f_to_str(self.alignment.y_offset)}")
        unaligned_boundary = self.alignment.unalign(self.wall.boundary)
        if wall_name == "Master Back" and name == 'star_+':
            print(f"Plan({wall_name}, {name}): ",
                  "unaligned_boundary=",
                  [f"({p[0]:.2f}, {p[1]:.2f})" for p in unaligned_boundary],
                  sep='')
        self.min_x = min(p[0] for p in unaligned_boundary)
        self.max_x = max(p[0] for p in unaligned_boundary)
        self.min_y = min(p[1] for p in unaligned_boundary)
        self.max_y = max(p[1] for p in unaligned_boundary)
        if wall_name == "Master Back" and name == 'star_+':
            print(f"Plan({wall_name}, {name}): "
                  f"min_x={self.min_x:.2f}, max_x={self.max_x:.2f}, "
                  f"min_y={self.min_y:.2f}, max_y={self.max_y:.2f}")

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
        self.do_step(self.layout,
                     dict(plan=self, offset=(-self.wall.diagonal, -self.wall.diagonal)))

    def align(self, points, offset):
        r'''Returns aligned points after applying offset.

        If the aligned points are not visible, returns None.
        '''
        aligned_points = self.alignment.align((x + offset[0], y + offset[1])
                                              for x, y in points)
        if self.wall.visible(aligned_points):
            return aligned_points
        return None

    def create_polygon(self, points, offset, color):
        r'''Does nothing if the points are not visible.

        Returns True if the points are visible, False otherwise.

        The `offset` is added to each point, and then the points are aligned
        before checking for visibility.
        '''
        aligned_points = self.align(points, offset)
        if aligned_points is None:
            return False
        item = app.canvas.create_my_polygon("plan", color, *aligned_points,
                                            tags=('tile',))
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
            print(f"{self.plan.name}.place(tile={tile}, angle={angle}, "
                  f"offset={constants['offset']})")
        the_tile = pick(tile, constants)
        if the_tile.place_at(constants['offset'], angle, self):
            constants['next_x'] = the_tile.skip_x + self.grout_gap
            constants['next_y'] = the_tile.skip_y + self.grout_gap
            return True
        return False

    def place_next(self, tile):
        r'''Returns next_x, next_y
        '''
        skip_x = get(tile, 'skip_x')
        if skip_x is not None:
            skip_x += self.grout_gap
        skip_y = get(tile, 'skip_y')
        if skip_y is not None:
            skip_y += self.grout_gap
        return skip_x, skip_y

    def sequence(self, constants, *steps, trace=False):
        r'''Returns True if any step is displayed, False if nothing is visible.

        If visible, returns the greatest next_x, next_y in constants.
        '''
        if trace:
            print(f"{self.name}.sequence({steps=})")
        visible = False
        next_x = next_y = None
        start_x, start_y = constants['offset']
        my_constants = ChainMap({}, constants)
        for step in steps:
            step = pick(step, constants)
            step_constants = my_constants.new_child()
            if 'use' in step:
                for key, value in step['use'].items():
                    step_constants[key] = my_eval(value, step_constants,
                                                  f"<Plan({self.name}).sequence: use {key}>")
            if 'offset' in step:
                x, y = my_eval(step['offset'], step_constants,
                               f"<Plan({self.name}).sequence: offset>")
                step_constants['offset'] = start_x + x, start_y + y
            else:
                step_constants['offset'] = start_x, start_y
            if self.do_step(step, step_constants, trace=trace):
                if 'save' in step:
                    for key, value in step['save'].items():
                        my_constants[key] = my_eval(value, step_constants,
                                                    f"<Plan({self.name}).sequence: save {key}>")
                if next_x is None or step_constants['next_x'] > next_x:
                    next_x = step_constants['next_x']
                if next_y is None or step_constants['next_y'] > next_y:
                    next_y = step_constants['next_y']
                visible = True
        if visible:
            constants['next_x'] = next_x
            constants['next_y'] = next_y
        return visible

    def sequence_next(self, steps):
        next_x_to_beat = next_y_to_beat = None
        next_x = next_y = -1000
        for step in steps:
            if not isinstance(step, (tuple, list)):
                step = [step]
            istep_next_x = istep_next_y = None
            istep_next = [self.get_step_next(istep) for istep in step]
            if next_x is not None:
                if any(p[0] is None for p in istep_next):
                    next_x = None
                else:
                    # FIX
                    pass
            if next_y is not None:
                if any(p[1] is None for p in istep_next):
                    next_y = None
                else:
                    # FIX
                    pass

    def repeat(self, constants, step, increment, times,
               step_width_limit, step_height_limit, trace=False):
        r'''Repeat step `times` times (infinite in both directions if times is None).

        `increment` is added to the offset after each repetition.

        Returns True if any repetition is visible, False if nothing is visible.

        If visible, returns the greatest next_x, next_y in constants.
        '''
        if trace:
            print(f"{self.name}.repeat({step=}, increment={f_to_str(increment)}, "
                  f"{times=}, {step_width_limit=}, {step_height_limit=})")
        visible = False
        min_x = self.min_x - 2 * step_width_limit
        max_x = self.max_x + step_width_limit
        min_y = self.min_y - 2 * step_width_limit
        max_y = self.max_y + step_width_limit
        next_x = next_y = None
        x_inc, y_inc = increment
        x, y = offset = constants['offset']
        print(f"repeat plan={self.name}, offset={f_to_str(offset)}, {times=}, "
              f"x_inc={f_to_str(x_inc)}, y_inc={f_to_str(y_inc)}")
        for index in (range(times) if times is not None else count(0)):
            print(f"repeat {index=}, offset={f_to_str(offset)}")
            if times is None:
                keep_going = x_inc > 0 and x <= max_x or \
                             x_inc < 0 and x >= min_x or \
                             y_inc > 0 and y <= max_y or \
                             y_inc < 0 and y >= min_y
                if not keep_going:
                    break
            constants['offset'] = offset
            constants['index'] = index
            if self.do_step(step, constants, trace=trace):
                if next_x is None or constants['next_x'] > next_x:
                    next_x = constants['next_x']
                if next_y is None or constants['next_y'] > next_y:
                    next_y = constants['next_y']
                visible = True
            x, y = offset = x + x_inc, y + y_inc
        if visible:
            constants['next_x'] = next_x
            constants['next_y'] = next_y
        print(f"repeat {visible=}, next_x={f_to_str(next_x)}, next_y={f_to_str(next_y)}")
        return visible

    def do_step(self, step, constants, trace=False):
        r'''Returns True if the step is visible, False otherwise.
        '''
        if trace:
            print(f"{self.name}.do_step({step=})")
        if 'next_x' in constants:
            del constants['next_x']
        if 'next_y' in constants:
            del constants['next_y']
        if step['type'] == 'place':
            return self.place(eval_tile(step['tile'], constants),
                              my_eval(step.get('angle', 0), constants,
                                      f"<Plan({self.name}).do_step: place angle>"),
                              constants, trace=trace)
        if step['type'] == 'sequence':
            return self.sequence(constants, *step['steps'], trace=trace)
        if step['type'] == 'repeat':
            x, y = my_eval(step.get('start', (0, 0)), constants,
                           f"<Plan({self.name}).do_step: repeat start>")
            x_off, y_off = constants['offset']
            print(f"do_step: repeat in plan({self.name}) "
                  f"x={f_to_str(x)}, y={f_to_str(y)}, "
                  f"x_off={f_to_str(x_off)}, y_off={f_to_str(y_off)}")
            constants['offset'] = x_off + x, y_off + y
            return self.repeat(constants, pick(step['step'], constants),
                               my_eval(step['increment'], constants,
                                 f"<Plan({self.name}).do_step: repeat increment>"),
                               my_eval(step.get('times', None), constants,
                                 f"<Plan({self.name}).do_step: repeat times>"),
                               my_eval(step.get('step_width_limit', 24), constants,
                                 f"<Plan({self.name}).do_step: repeat "
                                 "step_width_limit>"),
                               my_eval(step.get('step_height_limit', 24), constants,
                                 f"<Plan({self.name}).do_step: repeat "
                                 "step_height_limit>"),
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
                        print(f"{self.name}.lookup({arg}) in step -- "
                              f"value is {step[arg]}")
                    ans = my_eval(step[arg], constants,
                                  f"<Plan({self.name}).do_step: layout {step['type']} "
                                  f"{arg}>")
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
                    if trace or True:
                        print(f"{self.name}: add_constants adding {name=}, {value=}")
                    if name == 'conditionals':
                        for conditional in value:
                            test = my_eval(conditional['test'], new_constants,
                                           f"<Plan({self.name}).do_step: "
                                           f"layout {step['type']} conditionals test>")
                            if trace:
                                print(f"{self.name}: add_constants got "
                                      f"conditional {test=!r}, {conditional=}")
                            add_constants(conditional[test])
                    elif name == 'tile':
                        new_constants[name] = eval_tile(value, new_constants)
                    else:
                        new_constants[name] = my_eval(value, new_constants,
                                                f"<Plan({self.name}).do_step: "
                                                f"layout {step['type']} {name}>")
            add_constants(new_step['constants'])
        visible = self.do_step(new_step, new_constants, trace=trace)
        if visible:
            constants['next_x'] = new_constants['next_x']
            constants['next_y'] = new_constants['next_y']
        return visible

    def get_step_next(self, step):
        r'''Returns next_x, next_y

        If next_x or next_y is ambiguous, None is returned.
        '''
        if not isinstance(step, (tuple, list)):
            step = [step]
        for istep in step:
            type = istep['type']
            if type == 'place':
                return self.place_next(istep['tile'])
            if type == 'sequence':
                return self.sequence_next(istep['steps'])
            #if type == 'repeat':
            #   return self.repeat_next(istep[???])


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

