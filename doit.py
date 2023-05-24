# doit.py

from math import radians
from fractions import Fraction
from operator import attrgetter
from itertools import zip_longest
from functools import partial
import tkinter as tk
from tkinter import simpledialog, ttk

import app
from tile import Tile, erase_tiles
from utils import fraction, f_to_str, eval_color
from colors import read_colors
from shapes import read_shapes
from tiles import read_tiles
from layouts import read_layouts
from walls import read_walls
from settings import read_settings, save_settings


def tile_arg(s):
    name, width, height, color = s.split(',')
    return Tile.create(name, fraction(width), fraction(height), color)


class Dialog(simpledialog.Dialog):
    def __init__(self, master, title, fn, defaults, entries, **kwargs):
        self.fn = fn
        self.defaults = defaults
        self.entries = entries
        super().__init__(master, **kwargs)

    def body(self, master):
        print(f"Dialog.body: {master=}, {self.master=}")
        self.entry_widgets = []
        for i, ((name, entry_fn), default) \
         in enumerate(zip_longest(self.entries,
                                  self.defaults[:len(self.entries)],
                                  fillvalue=None)):
            tk.Label(master, text=name).grid(row=i, column=0)
            entry = entry_fn(master)
            entry.insert(0, default)
            self.entry_widgets.append(entry)
            entry.grid(row=i, column=1)
        if self.entry_widgets:
            return self.entry_widgets[0]

    def validate(self):
        print("Dialog.validate called")
        for entry in self.entry_widgets:
            if hasattr(entry, 'type_fn'):
                entry.value = entry.type_fn(entry.get())
            else:
                entry.value = entry.get()
        return 1  # 1 -> valid

    #def cancel(self):
    #    print("Dialog.cancel called")
    #    return 1  # hangs with or without return 1

    def apply(self):
        print("Dialog.apply called")
        for i, entry in enumerate(self.entry_widgets):
            if i >= len(self.defaults):
                self.defaults.append(entry.get())
            else:
                self.defaults[i] = entry.get()
        self.fn(self)

def run_dialog(title="Dialog Test", fn=lambda x: None, defaults=[], entries=()):
    print(f"run_dialog({title=!r})")
    dialog = Dialog(app.myapp, title, fn, defaults, entries)
    print("run_dialog -- DONE")


def str_entry(master):
    e = tk.Entry(master)
    e.type_fn = lambda x: x
    return e


def fraction_entry(master):
    e = tk.Entry(master)
    e.type_fn = fraction
    return e


def angle_entry(master):
    e = tk.Entry(master)
    e.type_fn = float
    return e


def color_entry(master):
    e = tk.Entry(master)
    e.type_fn = lambda s: eval_color(s, app.Colors)
    return e


def tile_entry(master):
    values = sorted(app.Tiles.keys())
    print(f"tile_entry {values=}")
    e = ttk.Combobox(master, values=values)
    e.type_fn = lambda s: app.Tiles[s]
    return e


def run_plan(name):
    app.Plan_name = name
    app.Plan = app.Plans[name]
    app.Plan.create()


Hop_defaults = [
    "12x24",              # tile_a
    "3x6",   # tile_b
    "1/8",                       # grout_gap
    "0",                         # angle
]

def run_hop():
    def do_hop(dialog):
        print("Adding hopscotch tiles")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        tile_a = values[0]
        tile_b = values[1]
        grout_gap = values[2]
        print(f"do_hop {grout_gap=}")
        angle = values[3]
        print(f"do_hop {angle=}")
        erase_tiles()
        hopscotch(tile_a, tile_b, grout_gap, angle, app.myapp.bg_width, app.myapp.bg_height)

    run_dialog("Hopscotch", do_hop, Hop_defaults, (
                  ("tile_a", tile_entry),
                  ("tile_b", tile_entry),
                  ("grout_gap", fraction_entry),
                  ("angle", angle_entry)))


Herr_defaults = [
    "12x24",       # tile
    "1/8",         # grout_gap
    "-45",         # angle
]

def run_herr():
    def do_herr(dialog):
        print("Adding herringbone tiles")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        tile_a = values[0]
        tile_b = tile_a.flipped
        grout_gap = values[1]
        print(f"do_herr {grout_gap=}")
        angle = values[2]
        print(f"do_herr {angle=}")
        erase_tiles()
        hopscotch(tile_a, tile_b, grout_gap, angle, app.myapp.bg_width, app.myapp.bg_height)

    run_dialog("Herringbone", do_herr, Herr_defaults, (
                  ("tile", tile_entry),
                  ("grout_gap", fraction_entry),
                  ("angle", angle_entry)))


Step_defaults = [
    "12x24",        # tile
    "0",            # offset    stacked
    "-8.1/4",       # x_offset  -8.3/8 on shower right wall
    "-5/8",         # y_offset
    "1/8",          # grout_gap  or 3/16
    "0",            # angle
]

# tile len w/o grout: 23.40625 == 23.13/32
# 1/3 step: 7.84375 == 7.27/32
# 1/2 of a 1/3 step: 3.921875 == 3.59/64

Step_defaults = [
    "12x24",        # tile
    "1/3",          # offset   1/2 doesn't work, 1/4 doesn't work (too busy)
    "-8.1/16",      # x_offset for back:
                    # -3.15/16 grout line at center of openings, slivers at walls and niche
                    # -4.15/16 grout line at center of wall, openings not centered
                    # 0 centered halfway, but on wrong row
                    # -7.7/8 centered halfway, has large sliver at window
                    # -9.1/2 "centered" halfway, no window sliver, looks centered on wall
  # "-8.3/16",      # x_offset for left: (checked)
  #                 # -8.3/16 grout line centerd on wall
  #                 # -4.17/64 full tile centered on wall
  # "-16.1/16",     # x_offset for right: (checked)
  #                 # -16.1/16 grout line on center of slide, lines up with back wall
  #                 # -12.9/64 center between grout lines centered on slide, lines up with
  #                 #          back wall
    "-3/4",         # y_offset
    "1/8",          # grout_gap
    "0",            # angle
]

Step_defaults = [
    "floor",        # tile
    "1/2",          # offset    stacked
    "0",            # x_offset  -1.1/2 grout line in center of entrance,
                    #           5.7/8 center on shower
    "-3.5/8",       # y_offset
    "1/8",          # grout_gap  or 3/16
    "0",            # angle
]

def run_step():
    def do_step(dialog):
        print("Adding stepped tiles")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        print(f"{values=}")
        tile = values[0]
        x_offset = values[2]
        y_offset = values[3]
        grout_gap = values[4]
        print(f"do_step {grout_gap=}")
        angle = values[5]
        print(f"do_step {angle=}")
        erase_tiles()
        if ',' in values[1]:
            offsets = tuple(map(fraction, values[1].split(',')))
            print(f"do_step {offsets=}")
            stepped2(tile, offsets, grout_gap, angle, x_offset, y_offset,
                     app.myapp.bg_width, app.myapp.bg_height)
        else:
            offset = fraction(values[1])
            print(f"do_step {offset=}")
            stepped(tile, offset, grout_gap, angle, x_offset, y_offset,
                    app.myapp.bg_width, app.myapp.bg_height)

    run_dialog("Stepped", do_step, Step_defaults, (
                  ("tile", tile_entry),
                  ("offset", str_entry),
                  ("x_offset", fraction_entry),
                  ("y_offset", fraction_entry),
                  ("grout_gap", fraction_entry),
                  ("angle", angle_entry)))


def run_set_grout_color():
    def do_grout_color(dialog):
        print("Setting grout color")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        color = values[0]
        print(f"do_grout_color {color=}")
        app.Plan.set_grout_color(color)

    run_dialog("Grout Color", do_grout_color, [app.Plan.grout_color], (
                  ("color", str_entry),))


def run_set_grout_gap():
    def do_grout_gap(dialog):
        print("Setting grout gap")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        gap = values[0]
        print(f"do_grout_gap {gap=}")
        app.Plan.grout_gap = gap
        app.Plan.create()

    run_dialog("Grout Gap", do_grout_gap, [app.Plan.grout_gap], (
                  ("gap", fraction_entry),))


def run_set_angle():
    def do_angle(dialog):
        print("Setting angle")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        angle = values[0]
        print(f"do_grout_color {angle=}")
        app.Plan.alignment.angle = angle
        app.Plan.create()

    run_dialog("Angle", do_angle, [app.Plan.alignment.angle], (
                  ("angle", angle_entry),))


def run_set_x_offset():
    def do_x_offset(dialog):
        print("Setting x_offset")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        x_offset = values[0]
        print(f"do_x_offset {x_offset=}")
        app.Plan.alignment.x_offset = x_offset
        app.Plan.create()

    run_dialog("X_offset", do_x_offset, [app.Plan.alignment.x_offset], (
                  ("x_offset", fraction_entry),))

def run_set_y_offset():
    def do_y_offset(dialog):
        print("Setting y_offset")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        y_offset = values[0]
        print(f"do_y_offset {y_offset=}")
        app.Plan.alignment.y_offset = y_offset
        app.Plan.create()

    run_dialog("Y_offset", do_y_offset, [app.Plan.alignment.y_offset], (
                  ("y_offset", fraction_entry),))


def init():
    print("doit.init called")

    app.Colors = read_colors()
    app.Shapes = read_shapes()
    app.Tiles = read_tiles()
    app.Layouts = read_layouts()
    app.Walls = read_walls()
    app.Settings = read_settings()
    wall = app.myapp.submenus['Wall']
    wall.delete(0, 'end')
    for name in sorted(app.Walls.keys()):
        wall.add_command(label=name, command=partial(create_wall, name))

    app.Wall_name = None
    app.Wall = None
    app.Plan_name = None
    app.Plan = None


def reload():
    wall_name = app.Wall_name
    plan_name = app.Plan_name
    init()
    if wall_name is None and 'default_wall' in app.settings:
        wall_name = app.settings['default_wall']
        plan_name = None
    if wall_name is not None:
        create_wall(wall_name, plan_name)


def save_settings():
    app.Settings



if __name__ == "__main__":
    import argparse
    from tkinter import colorchooser

    parser = argparse.ArgumentParser()
    #parser.add_argument("tile_a", type=tile_arg, help="name,width,height,color")
    #parser.add_argument("tile_b", type=tile_arg, help="name,width,height,color")
    #parser.add_argument("grout_gap", type=fraction, help="I or I.N/D or N/D")

    args = parser.parse_args()

    def choose_color():
        print(f"choose_color -> {colorchooser.askcolor()}")

    def create_wall(name, plan_name=None):
        app.Wall_name = name
        app.Wall = app.Walls[name]
        app.Wall_settings = app.Settings['wall_settings'][name]
        app.Plans = app.Wall_settings['plans']
        app.Wall.create()

        plans = app.myapp.submenus['Plans']
        plans.delete(0, 'end')
        for name, plan in app.Plans.items():
            plans.add_command(label=name, command=partial(run_plan, name))
        if plan_name is None and 'default_plan' in app.Wall_settings:
            plan_name = app.Wall_settings['default_plan']
        if plan_name is not None:
            run_plan(app.Wall_settings[plan_name])

    def quit():
        app.root.destroy()

    app.init((("Quit", quit),
              ("Spew", app.spew),
              ("Reload", reload),
             #("Dialog Test", run_dialog),
              ("Choose Color", choose_color),
              ("Wall",),
              ("Plans",),
              ("Plan Settings", (
                 ("Set Grout Color", run_set_grout_color),
                 ("Set Grout Gap", run_set_grout_gap),
                 ("Set Angle", run_set_angle),
                 ("Set X_offset", run_set_x_offset),
                 ("Set Y_offset", run_set_y_offset),
              )),
              ("Save Settings", save_settings),
            ))

    init()

    app.run()

