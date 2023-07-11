# plan.py

from collections import ChainMap, Counter
from itertools import count

import app
from utils import my_eval, eval_pair, eval_color, eval_tile, format, f_to_str, pick, unpick
from tile import erase_tiles
from alignment import Alignment
from place_trace import pt_init, place


class Plan:
    attrs = 'grout_gap,grout_color,alignment,layout'.split(',')

    def __init__(self, name, plan, canvas, constants):
        self.name = name
        self.canvas = canvas
        for attr in self.attrs:
            try:
                value = plan[attr]
            except KeyError:
                if attr == 'grout_color':
                    value = None
                else:
                    raise
            if attr == 'alignment':
                value = Alignment(value, constants)
            elif attr == 'grout_gap':
                value = my_eval(value, constants, f"<Plan({name}): {attr}>")
            setattr(self, attr, value)

    def __repr__(self):
        return f"<Plan: {self.name}>"

    def dump(self):
        return {attr: (format(getattr(self, attr)) 
                       if attr != 'alignment'
                       else getattr(self, attr).dump())
                for attr in self.attrs}

    def set_grout_color(self, color):
        assert self.grout_color is not None, f"Plan({self.name}) does not have a grout_color"
        self.grout_color = color
        self.display_grout_color()

    def display_grout_color(self):
        if app.Plan == self:
            color = eval_color(self.grout_color)
            self.canvas.itemconfig("grout", fill=color)
            self.canvas.current_grout_color = color
            def do_sections(canvas):
                for item in canvas.find_withtag('section'):
                    section = app.root.nametowidget(canvas.itemcget(item, 'window'))
                    print("section", section)
                    print(dir(section))
                    section.configure(bg=color)
                    section.current_grout_color = color
                    do_sections(section)
            do_sections(self.canvas)

    def create(self, constants=None, trace=()):
        erase_tiles(self.canvas)
        self.display_grout_color()
        pt_init()
        app.Counters = Counter()
        #new_constants = dict(plan=self, offset=(-self.canvas.diagonal,
        #                                        -self.canvas.diagonal)))
        new_constants = dict(wall=app.Wall, plan=self, offset=(0, 0))
        if constants is not None:
            new_constants = ChainMap(new_constants, constants)
        self.do_step(f"Plan({self.name})", self.layout, new_constants, trace=trace)

    def get_inc_xy(self, steps, constants, location=None):
        r'''Includes grout gaps up to (but not beyond) the final edge.
        '''
        hold_alignment = self.alignment
        self.alignment = Alignment(dict(angle=0,x_offset=0,y_offset=0), {})
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
                inc_y = None
                y_dead = True
        assert not x_dead and not y_dead, \
               f"get_inc_xy {location}: {x_dead=}, {y_dead=}"
        if location is not None:
            print(f"get_inc_xy {location=}: "
                  f"inc_x={f_to_str(inc_x)}, inc_y={f_to_str(inc_y)}")
        self.alignment = hold_alignment
        return inc_x, inc_y

    def align(self, points, offset):
        r'''Returns aligned points after applying offset.

        If the aligned points are not visible, returns None.
        '''
        aligned_points = self.alignment.align((x + offset[0], y + offset[1])
                                              for x, y in points)
        if self.canvas.visible(aligned_points):
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
            item = self.canvas.create_my_polygon("plan", color, *aligned_points,
                                                 tags=('tile',))
            if self.canvas.find_withtag("topmost"):
                self.canvas.tag_lower(item, "topmost")
        return True

    def create_image(self, image, sw_offset, pos):
        item = self.canvas.create_my_image("plan", image, sw_offset, pos, tags=('tile',))
        if self.canvas.find_withtag("topmost"):
            self.canvas.tag_lower(item, "topmost")

    def place(self, step_name, tile, angle, constants, trace=()):
        r'''Returns True if displayed, False if not visible.

        If visible, updates `inc_x` and `inc_y` in `constants` (including grout_gap).
        '''
        if 'place' in trace:
            print(f"{step_name}.place(tile={tile}, angle={angle}, "
                  f"offset={f_to_str(constants['offset'])})")
        the_tile = pick(tile, constants, 'tile')
        visible = the_tile.place_at(constants['offset'], pick(angle, constants, 'angle'), self,
                                    constants.get('skip', False))
        place(constants['offset'], visible)
        if visible:
            constants['inc_x'] = the_tile.skip_x + self.grout_gap
            constants['inc_y'] = the_tile.skip_y + self.grout_gap
            if 'place' in trace or 'place_true' in trace:
                print(f"{step_name}.place {the_tile.name=} -> True, "
                      f"offset={f_to_str(constants['offset'])}")
            return True
        unpick(constants, 'tile')
        unpick(constants, 'angle')
        if 'place' in trace:
            print(f"{step_name}.place -> False")
        return False

    def sequence(self, step_name, constants, *steps, trace=()):
        r'''Returns True if any step is displayed, False if nothing is visible.

        If visible, returns the greatest inc_x, inc_y in constants.

        The sequence executes with it's own constants that are discarded when it's done.
        Additionally, each step executes with it's own disposable constants.

        The initial offset is stored as constants in 'initial_x', 'initial_y'.  These are
        used for the offset fed to each step.

        Individual steps may be skipped by setting skip: true on the step.
        '''
        visible = False
        inc_x = inc_y = None
        initial_x, initial_y = constants['offset']
        if 'sequence' in trace:
            print(f"{step_name}.sequence: "
                  f"initial_x={f_to_str(initial_x)}, initial_y={f_to_str(initial_y)}")

        # These are passed on from one step to the next with save/use.
        my_constants = ChainMap({}, constants)
        my_constants['initial_x'] = initial_x
        my_constants['initial_y'] = initial_y

        for i, step in enumerate(steps, 1):
            #print(f"{step_name}.sequence: step {i}, {step=}, {constants=}")
            step = pick(step, constants, 'step')
            if my_eval(step.get('skip', False), constants, f"<{step_name}.sequence: skip"):
                continue
            step_constants = my_constants.new_child()
            step_constants['offset'] = initial_x, initial_y
            if 'offset' in trace:
                print(f"sequence step {i}: offset={f_to_str(step_constants['offset'])}")
            if self.do_step(f"sequence, step {i}", step, step_constants, trace=trace):
                offset_x, offset_y = step_constants['offset']
                if inc_x is None or step_constants['inc_x'] + offset_x > inc_x:
                    inc_x = step_constants['inc_x'] + offset_x
                    if 'inc_x' in trace:
                        print(f"{step_name}.sequence step {i}: "
                              f"got inc_x {f_to_str(step_constants['inc_x'])}, "
                              f"offset_x {f_to_str(offset_x)}, inc_x set to {f_to_str(inc_x)}")
                if inc_y is None or step_constants['inc_y'] + offset_y > inc_y:
                    inc_y = step_constants['inc_y'] + offset_y
                    if 'inc_y' in trace:
                        print(f"{step_name}.sequence step {i}: inc_y set to {f_to_str(inc_y)}")
                visible = True
            else:
                unpick(constants, 'step')
            #else:
            #    print(f"{step_name}.sequence step {i}: not visible")
        if visible:
            constants['inc_x'] = inc_x
            constants['inc_y'] = inc_y
            if 'sequence' in trace:
                print(f"{step_name}.sequence -> "
                      f"inc_x={f_to_str(constants['inc_x'])}, inc_y={f_to_str(constants['inc_y'])}")
        if 'sequence' in trace:
            print(f"{step_name}.sequence -> {visible=}")
        return visible

    def repeat(self, step_name, constants, step, increment, times,
               step_width_limit, step_height_limit, index_start, trace=()):
        r'''Repeat step `times` times (infinite in both directions if times is None).

        `increment` is added to the offset after each repetition.

        Returns True if any repetition is visible, False if nothing is visible.

        If visible, returns the greatest inc_x, inc_y in constants.
        '''
        if 'repeat' in trace:
            print(f"{step_name}({step=}, "
                  f"offset={f_to_str(constants['offset'])}, "
                  f"increment={f_to_str(increment)}, {times=}, "
                  f"{step_width_limit=}, {step_height_limit=}, {index_start=})")
        if True:
            unaligned_boundary = self.alignment.unalign(self.canvas.boundary)
            #print(f"{step_name}: "
            #      f"unaligned_boundary={f_to_str(unaligned_boundary)}")
            min_x = min(p[0] for p in unaligned_boundary) - 2 * step_width_limit
            max_x = max(p[0] for p in unaligned_boundary) + step_width_limit
            min_y = min(p[1] for p in unaligned_boundary) - 2 * step_height_limit
            max_y = max(p[1] for p in unaligned_boundary) + step_height_limit
        else:
            min_x = min_y = -self.canvas.diagonal - 2 * step_width_limit
            max_x = max_y = self.canvas.diagonal + step_width_limit
        #print(f"{step_name}: "
        #      f"min_x={min_x:.2f}, max_x={max_x:.2f}, "
        #      f"min_y={min_y:.2f}, max_y={max_y:.2f}")
        visible = False
        inc_x = inc_y = None
        x_inc, y_inc = increment
        if 'xy_inc' in trace:
            print(f"{step_name} x_inc={f_to_str(x_inc)}, "
                  f"min_x={f_to_str(min_x)}, max_x={f_to_str(max_x)}")
            print(f"{step_name} y_inc={f_to_str(y_inc)}, "
                  f"min_y={f_to_str(min_y)}, max_y={f_to_str(max_y)}")
        x, y = constants['offset']
        if 'xy' in trace:
            print(f"{step_name} initial offset: x={f_to_str(x)}, y={f_to_str(y)}")
        if times is None:
            # Back up x, y until they're before min/max ranges.
            #
            # Use index to also back up index_start.
            for index in count(0):
                keep_going = (x_inc == 0 and min_x <= x <= max_x or
                              x_inc > 0 and x >= min_x or \
                              x_inc < 0 and x <= max_x) and \
                             (y_inc == 0 and min_y <= y <= max_y or
                              y_inc > 0 and y >= min_y or \
                              y_inc < 0 and y <= max_y)
                if not keep_going:
                    break
                x, y = x - x_inc, y - y_inc
                if index > 100:
                    print(f"{step_name}: x={f_to_str(x)}, x_inc={f_to_str(x_inc)}")
                    print(f"{step_name}: y={f_to_str(y)}, y_inc={f_to_str(y_inc)}")
                    raise AssertionError(f"{step_name}: {index=} out of bounds backing up")
            index_start -= index
            if 'xy' in trace:
                print(f"{step_name} adjusted starting offset: x={f_to_str(x)}, y={f_to_str(y)}, {index_start=}")
        offset = starting_offset = x, y

        for index in (range(times) if times is not None else count(0)):
            #print(f"{step_name} {index=}, offset={f_to_str(offset)}")
            constants['offset'] = offset
            constants['index'] = index + index_start
            step_visible = self.do_step(f"repeat {index=}", pick(step, constants, 'step'),
                                        constants, trace=(trace if index < 3 else ()))
            if step_visible:
                step_inc_x = constants['inc_x'] + index * x_inc
                step_inc_y = constants['inc_y'] + index * y_inc
                if inc_x is None or step_inc_x > inc_x:
                    inc_x = step_inc_x
                if inc_y is None or step_inc_y > inc_y:
                    inc_y = step_inc_y
                visible = True
            else:
                unpick(constants, 'step')
            if times is None:
                keep_going = step_visible or \
                             (x_inc == 0 and min_x <= x <= max_x or
                              x_inc > 0 and x <= max_x or \
                              x_inc < 0 and x >= min_x) and \
                             (y_inc == 0 and min_y <= y <= max_y or
                              y_inc > 0 and y <= max_y or \
                              y_inc < 0 and y >= min_y)
                if not keep_going:
                    break
            if index > 100:
                print(f"{step_name} x={f_to_str(x)}, x_inc={f_to_str(x_inc)}, "
                      f"min_x={f_to_str(min_x)}, max_x={f_to_str(max_x)}")
                print(f"{step_name} y={f_to_str(y)}, y_inc={f_to_str(y_inc)}, "
                      f"min_y={f_to_str(min_y)}, max_y={f_to_str(max_y)}")
                raise AssertionError(f"{step_name}: {index=} out of bounds, {step_visible=}")
            x, y = offset = x + x_inc, y + y_inc
            if 'xy' in trace:
                print(f"{step_name} x={f_to_str(x)}, y={f_to_str(y)}, {step_visible=}, {index=}")
        if visible:
            constants['inc_x'] = inc_x
            constants['inc_y'] = inc_y
        #print(f"{step_name}: {visible=}, inc_x={f_to_str(inc_x)}, "
        #      f"inc_y={f_to_str(inc_y)}")
        if 'repeat' in trace:
            print(f"{step_name} -> {visible=}")
        return visible

    def section(self, step_name, step, pos, size, constants, trace=()):
        print(f"section {step_name=}, pos={f_to_str(pos)}, size={f_to_str(size)}")
        if not isinstance(step, dict):
            print(f"section got {step=}, expected dict")
        canvas, item = self.canvas.create_canvas("section", pos, size, tags=('section',))
        if self.canvas.find_withtag("topmost"):
            self.canvas.tag_lower(item, "topmost")
        plan = Plan(step_name, step, canvas, constants)
        plan.create(constants, trace=trace)

    def do_step(self, step_name, step, constants, trace=()):
        r'''Returns True if the step is visible, False otherwise.

        `offset` is the final position to place the lower-left corner of the step.  This can be
        specified directly in the step to completely override the offset it was given.

        The step may add a `delta` to whatever offset it is given.  This can also be specified
        as `delta_x` and/or `delta_y`.

        Do not specify `offset`, `delta`, `delta_x` or `delta_y` in `constants`.
        '''
        if 'trace' in step:
            trace = tuple(step['trace'])
        if 'name' in step:
            step_name = step['name']
        if 'do_step' in trace:
            print(f"{self.name}.do_step({step_name=}, {step=})")
        if 'inc_x' in constants:
            constants['inc_x'] = None
        if 'inc_y' in constants:
            constants['inc_y'] = None
        if 'index_by_counter' in constants:
            constants['index_by_counter'] = None
        new_constants = ChainMap({}, constants)
        if 'index_by_counter' in step:
            new_constants['index_by_counter'] = step['index_by_counter']
        self.load_constants(new_constants, step, f"do_step {step_name} load_constants", trace)
        if 'offset' in step:
            constants['offset'] = eval_pair(step['offset'], new_constants,
                                            f"<{step_name}.do_step: offset>")
        else:
            if 'delta' in step:
                delta = eval_pair(step['delta'], new_constants, f"<{step_name}.do_step: delta>")
            else:
                delta = (my_eval(step.get('delta_x', 0), new_constants,
                                 f"<{step_name}.do_step: delta_x>"),
                         my_eval(step.get('delta_y', 0), new_constants,
                                 f"<{step_name}.do_step: delta_y>"))
            if 'delta' in trace:
                print(f"do_step {step_name}: delta={f_to_str(delta)}")
            constants['offset'] = (constants['offset'][0] + delta[0], 
                                   constants['offset'][1] + delta[1])
        if 'offset' in trace:
            print(f"do_step {step_name}: offset={f_to_str(constants['offset'])}")
        if step['type'] == 'place':
            visible = self.place(step_name, eval_tile(step['tile'], new_constants),
                                 my_eval(step.get('angle', 0), new_constants,
                                         f"<{step_name}.do_step: place angle>"),
                                 new_constants, trace=trace)
            if visible:
                constants['inc_x'] = new_constants['inc_x']
                constants['inc_y'] = new_constants['inc_y']
                if 'inc_x' in trace:
                    print(f"do_step {step_name}: inc_x={f_to_str(constants['inc_x'])}")
                if 'inc_y' in trace:
                    print(f"do_step {step_name}: inc_y={f_to_str(constants['inc_y'])}")
            return visible
        if step['type'] == 'sequence':
            visible = self.sequence(step_name, new_constants, *step['steps'], trace=trace)
            if visible:
                constants['inc_x'] = new_constants['inc_x']
                constants['inc_y'] = new_constants['inc_y']
                if 'inc_x' in trace:
                    print(f"do_step {step_name}: inc_x={f_to_str(constants['inc_x'])}")
                if 'inc_y' in trace:
                    print(f"do_step {step_name}: inc_y={f_to_str(constants['inc_y'])}")
            return visible
        if step['type'] == 'repeat':
            x, y = my_eval(step.get('start', (0, 0)), new_constants,
                           f"<{step_name}.do_step: repeat start>")
            x_off, y_off = new_constants['offset']
            #print(f"do_step: repeat in {step_name} "
            #      f"x={f_to_str(x)}, y={f_to_str(y)}, "
            #      f"x_off={f_to_str(x_off)}, y_off={f_to_str(y_off)}")
            new_constants['offset'] = x_off + x, y_off + y
            visible = self.repeat(step_name, new_constants,
                                  my_eval(step['step'], new_constants,
                                    f"{step_name} repeat step"),
                                  my_eval(step['increment'], new_constants,
                                    f"<{step_name}.do_step: repeat increment>"),
                                  my_eval(step.get('times', None), new_constants,
                                    f"<{step_name}.do_step: repeat times>"),
                                  my_eval(step.get('step_width_limit', 24), new_constants,
                                    f"<{step_name}.do_step: repeat "
                                    "step_width_limit>"),
                                  my_eval(step.get('step_height_limit', 24), new_constants,
                                    f"<{step_name}.do_step: repeat step_height_limit>"),
                                  my_eval(step.get('index_start', 0), new_constants,
                                    f"<{step_name}.do_step: repeat index_start>"),
                                  trace=trace)
            if visible:
                constants['inc_x'] = new_constants['inc_x']
                constants['inc_y'] = new_constants['inc_y']
                if 'inc_x' in trace:
                    print(f"do_step {step_name}: inc_x={f_to_str(constants['inc_x'])}")
                if 'inc_y' in trace:
                    print(f"do_step {step_name}: inc_y={f_to_str(constants['inc_y'])}")
            return visible
        if step['type'] == 'section':
            visible = self.section(step_name, step,
                                   eval_pair(step['pos'], new_constants,
                                     f"<{step_name}.do_step: section pos>"),
                                   eval_pair(step['size'], new_constants,
                                     f"<{step_name}.do_step: section size>"),
                                   new_constants, trace=trace)
            if visible:
                constants['inc_x'] = new_constants['inc_x']
                constants['inc_y'] = new_constants['inc_y']
                if 'inc_x' in trace:
                    print(f"do_step {step_name}: inc_x={f_to_str(constants['inc_x'])}")
                if 'inc_y' in trace:
                    print(f"do_step {step_name}: inc_y={f_to_str(constants['inc_y'])}")
            return visible

        # else it's a call to a layout
        new_step = app.Layouts[step['type']]
        if 'trace' in new_step:
            trace += tuple(new_step['trace'])
        def lookup(param, defaults):
            if param in step:
                if param in ('tile', 'tiles') or param.startswith('tile_'):
                    if 'lookup' in trace:
                        print(f"{step_name}.lookup({param}) in step -- tile! "
                              f"-- value is {step[param]}")
                    ans = eval_tile(step[param], new_constants)
                    #print(f"{step['type']}: setting {param=}, {step[param]=} to {ans}")
                else:
                    if 'lookup' in trace:
                        print(f"{step_name}.lookup({param}) in step -- "
                              f"value is {step[param]}")
                    ans = my_eval(step[param], new_constants,
                                  f"<{step_name}.do_step: layout {step['type']} "
                                  f"{param}>")
            #elif param in new_constants:
            #    if 'lookup' in trace:
            #        print(f"{step_name}.lookup({param}) in constants "
            #              f"-- value is {f_to_str(constants[param])}")
            #    ans = constants[param]
            elif param in defaults:
                ans = my_eval(defaults[param], new_constants,
                              f"<{step_name}.do_step: layout {step['type']} "
                              f"defaults {param}>")
            else:
                ans = None
            if 'lookup' in trace:
                print(f"{step['type']}: setting parameter {param} to {f_to_str(ans)}")
            return ans
        if 'defaults' in new_step:
            defaults = new_step['defaults']
        else:
            defaults = {}
        #print(f"{step['type']} {defaults=}")
        for param in new_step.get('parameters', ()):
            new_constants[param] = lookup(param, defaults)
        #new_constants['plan'] = self
        #new_constants['offset'] = constants['offset']
        self.load_constants(new_constants, new_step, f"layout {step['type']} load_constants", trace)
        visible = self.do_step(step['type'], new_step, new_constants, trace=trace)
        if visible:
            constants['inc_x'] = new_constants['inc_x']
            constants['inc_y'] = new_constants['inc_y']
            if 'inc_x' in trace:
                print(f"do_step {step_name}: inc_x={f_to_str(constants['inc_x'])}")
            if 'inc_y' in trace:
                print(f"do_step {step_name}: inc_y={f_to_str(constants['inc_y'])}")
        return visible

    def load_constants(self, new_constants, step, location, trace):
        if 'constants' in step:
            def add_constants(constants):
                for name, value in constants.items():
                    if name == 'conditionals':
                        for conditional in value:
                            test = my_eval(conditional['test'], new_constants,
                                           location + "conditionals test")
                            if 'constants' in trace:
                                print(f"{location}: add_constants got "
                                      f"{conditional=}, {test=!r}")
                            if test in conditional:
                                add_constants(conditional[test])
                            else:
                                add_constants(conditional['else'])
                    else:
                        if name in ('tile', 'tiles') or name.startswith('tile_'):
                            new_constants[name] = eval_tile(value, new_constants)
                        else:
                            new_constants[name] = my_eval(value, new_constants,
                                                    location + f"{name}>")
                        if 'constants' in trace or name in trace:
                            print(f"{location} adding {name=}, value={f_to_str(new_constants[name])}")
            add_constants(step['constants'])
        #print(f"{location}: new_constants={f_to_str(new_constants)}")
