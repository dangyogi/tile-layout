# doit.py

from operator import attrgetter
from itertools import zip_longest
from functools import partial
import tkinter as tk
from tkinter import simpledialog, ttk

import app
from utils import fraction, f_to_str, eval_color
from colors import read_colors
from shapes import read_shapes
from tiles import read_tiles
from layouts import read_layouts
from walls import read_walls
from settings import read_settings
from place_trace import dump_stats



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
    values = sorted(app.Colors.keys())
    e = ttk.Combobox(master, values=values)
    e.type_fn = lambda s: s
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
    app.root.title(f"{app.Wall_name}: {name}")
    app.Plan.create()


def run_set_grout_color():
    def do_grout_color(dialog):
        print("Setting grout color")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        color = values[0]
        print(f"do_grout_color {color=}")
        app.Plan.set_grout_color(color)

    run_dialog("Grout Color", do_grout_color, [app.Plan.grout_color], (
                  ("color", color_entry),))


def run_set_grout_gap():
    def do_grout_gap(dialog):
        print("Setting grout gap")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        gap = values[0]
        print(f"do_grout_gap {gap=}")
        app.Plan.grout_gap = gap
        app.Plan.create()

    run_dialog("Grout Gap", do_grout_gap, [f_to_str(app.Plan.grout_gap)], (
                  ("gap", fraction_entry),))


def run_set_angle():
    def do_angle(dialog):
        print("Setting angle")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        angle = values[0]
        print(f"do_angle {angle=}")
        app.Plan.alignment.set_angle(angle)
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

    run_dialog("X_offset", do_x_offset, [f_to_str(app.Plan.alignment.x_offset)], (
                  ("x_offset", fraction_entry),))

def run_set_y_offset():
    def do_y_offset(dialog):
        print("Setting y_offset")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        y_offset = values[0]
        print(f"do_y_offset {y_offset=}")
        app.Plan.alignment.y_offset = y_offset
        app.Plan.create()

    run_dialog("Y_offset", do_y_offset, [f_to_str(app.Plan.alignment.y_offset)], (
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
    if wall_name is None and 'default_wall' in app.Settings:
        wall_name = app.Settings['default_wall']
        plan_name = None
    if wall_name is not None:
        create_wall(wall_name, plan_name)



if __name__ == "__main__":
    import argparse
    from tkinter import colorchooser

    parser = argparse.ArgumentParser()
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
            run_plan(plan_name)
        else:
            app.root.title(name)

    def quit():
        app.root.destroy()
        dump_stats()

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
              ("Dump Stats", dump_stats),
            ))

    init()

    app.run()

