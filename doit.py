# doit.py

from math import radians
from fractions import Fraction
from operator import attrgetter
from itertools import zip_longest
import tkinter as tk
from tkinter import simpledialog

import app
from hopscotch import hopscotch
from stepped import stepped
from tile import Tile, erase_tiles
from utils import fraction, eval_color


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


def fraction_entry(master):
    e = tk.Entry(master)
    e.type_fn = fraction
    return e


def angle_entry(master):
    e = tk.Entry(master)
    e.type_fn = lambda s: radians(float(s))
    return e


def color_entry(master):
    e = tk.Entry(master)
    e.type_fn = lambda s: eval_color(s, Colors)
    return e


Hop_defaults = [
    "big",     # tile_a: name
    "9.7/8",   # tile_a: width
    "4.1/4",   # tile_a: height
    "black",   # tile_a: color
    "small",   # tile_b: name
    "4.1/4",   # tile_b: width
    "1",       # tile_b: height
    "#b0b000", # tile_b: color
    "1/4",     # grout_gap
    "7",       # angle
]

def run_hop():
    def do_hop(dialog):
        print("Adding hopscotch tiles")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        print(f"do_hop creating tile_a: {values[0:4]=}")
        tile_a = Tile.create(*values[0:4])
        print(f"do_hop creating tile_b: {values[4:8]=}")
        tile_b = Tile.create(*values[4:8])
        grout_gap = values[8]
        print(f"do_hop {grout_gap=}")
        angle = values[9]
        print(f"do_hop {angle=}")
        erase_tiles()
        hopscotch(tile_a, tile_b, grout_gap, angle, bg_width, bg_height)

    run_dialog("Hopscotch", do_hop, Hop_defaults, (
                  ("tile_a: name", tk.Entry),
                  ("tile_a: width", fraction_entry),
                  ("tile_a: height", fraction_entry),
                  ("tile_a: color", color_entry),

                  ("tile_b: name", tk.Entry),
                  ("tile_b: width", fraction_entry),
                  ("tile_b: height", fraction_entry),
                  ("tile_b: color", color_entry),

                  ("grout_gap", fraction_entry),
                  ("angle", angle_entry)))


Herr_defaults = [
    "big",     # tile: name
    "9.7/8",   # tile: width
    "4.1/4",   # tile: height
    "black",   # tile: color
    "1/4",     # grout_gap
    "-45",     # angle
]

def run_herr():
    def do_herr(dialog):
        print("Adding herringbone tiles")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        print(f"do_herr creating tile_a: {values[0:4]=}")
        tile_a = Tile.create(*values[0:4])
        tile_b = Tile.create(values[0], values[2], values[1], values[3])
        grout_gap = values[4]
        print(f"do_herr {grout_gap=}")
        angle = values[5]
        print(f"do_herr {angle=}")
        erase_tiles()
        hopscotch(tile_a, tile_b, grout_gap, angle, bg_width, bg_height)

    run_dialog("Herringbone", do_herr, Herr_defaults, (
                  ("tile: name", tk.Entry),
                  ("tile: width", fraction_entry),
                  ("tile: height", fraction_entry),
                  ("tile: color", color_entry),

                  ("grout_gap", fraction_entry),
                  ("angle", angle_entry)))


Step_defaults = [
    "big",      # tile: name
    "9.7/8",    # tile: width
    "4.1/4",    # tile: height
    "black",    # tile: color
    "1/3",      # offset
    "1/4",      # grout_gap
    "11",       # angle
]

def run_step():
    def do_step(dialog):
        print("Adding stepped tiles")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        print(f"do_step creating tile: {values[0:4]=}")
        tile = Tile.create(*values[0:4])
        offset = values[4]
        print(f"do_step {offset=}")
        grout_gap = values[5]
        print(f"do_step {grout_gap=}")
        angle = values[6]
        print(f"do_step {angle=}")
        erase_tiles()
        stepped(tile, offset, grout_gap, angle, bg_width, bg_height)

    run_dialog("Stepped", do_step, Step_defaults, (
                  ("tile: name", tk.Entry),
                  ("tile: width", fraction_entry),
                  ("tile: height", fraction_entry),
                  ("tile: color", color_entry),

                  ("offset", fraction_entry),
                  ("grout_gap", fraction_entry),
                  ("angle", angle_entry)))


Grout_color_defaults = [
    "joyful orange",       # color
]

def run_set_grout_color():
    def do_grout_color(dialog):
        print("Setting grout color")
        values = tuple(map(attrgetter('value'), dialog.entry_widgets))
        color = values[0]
        print(f"do_grout_color {color=}")
        app.canvas.itemconfig("grout", fill=color)

    run_dialog("Grout Color", do_grout_color, Grout_color_defaults, (
                  ("color", color_entry),))


if __name__ == "__main__":
    import argparse
    from tkinter import colorchooser

    parser = argparse.ArgumentParser()
    #parser.add_argument("tile_a", type=tile_arg, help="name,width,height,color")
    #parser.add_argument("tile_b", type=tile_arg, help="name,width,height,color")
    #parser.add_argument("grout_gap", type=fraction, help="I or I.N/D or N/D")

    args = parser.parse_args()

    from colors import read_colors

    Colors = read_colors()

    cabinet = Colors['cabinet']
    silver = Colors['silver']
    grout_color = Colors['joyful orange']

    def choose_color():
        print(f"choose_color -> {colorchooser.askcolor()}")

    def grout_bg(width, height, color=grout_color):
        global bg_width, bg_height
        bg_width = width              # inches
        bg_height = height            # inches
        app.canvas.delete("all")
        app.myapp.scale_width(bg_width)
        app.myapp.create_rectangle(0, 0, bg_width, bg_height, color, ("background", "grout"))
        bg_color = app.canvas.cget('background')

        # clip above grout background
        if app.canvas.height > app.myapp.in_to_px(bg_height):
            app.myapp.create_rectangle(0, bg_height,
                                       app.canvas.width, app.canvas.height - bg_height,
                                       bg_color, ("background", "topmost"))

        # clip to the right of grout background
        #if app.canvas.width > app.myapp.in_to_px(bg_width):
        #    app.myapp.create_rectangle(bg_width, 0,
        #                               app.canvas.width - bg_width, bg_height,
        #                               bg_color, ("background", "topmost"))

    def sink():
        print("Adding sink background")
        grout_bg(fraction("96.1/16"), fraction("17.1/2"))
        app.myapp.create_rectangle(0, fraction("17.3/8"),
                                   fraction("31.1/4"), 37,
                                   cabinet, ("background", "topmost"))       # left cab
        cab_width = fraction("32.3/4")
        app.myapp.create_rectangle(bg_width-cab_width, fraction("17.1/2"),
                                   cab_width, fraction("36.1/2"),
                                   cabinet, ("background", "topmost"))       # right cab
        app.myapp.create_rectangle(fraction("32.7/16"), fraction("9.3/8"),
                                   fraction("29.3/4"), fraction("26.1/2"),
                                   "#CCC", ("background", "topmost"))        # window

    def stove():
        print("Adding stove background")
        grout_bg(96, fraction("17.1/2"))
        lt_cab_width = fraction("19.1/4")
        app.myapp.create_rectangle(0, fraction("17.1/2"),
                                   lt_cab_width, fraction("36.7/8"),
                                   cabinet, ("background", "topmost"))       # left cab
        rt_cab_width = fraction("46.7/8")
        rt_cab_height = fraction("36.3/4")
        app.myapp.create_rectangle(bg_width-rt_cab_width, fraction("17.1/2"),
                                   rt_cab_width, rt_cab_height,
                                   cabinet, ("background", "topmost"))       # right cab
        uw_offset = fraction("19.1/8")
        uw_height = fraction("16.7/8")
        app.myapp.create_rectangle(lt_cab_width, uw_offset,
                                   30, uw_height,
                                   silver, ("background", "topmost"))        # uWave
        app.myapp.create_rectangle(lt_cab_width, uw_offset + uw_height,
                                   30, fraction("35.1/4") - uw_height,
                                   cabinet, ("background", "topmost"))       # cab over uWave
        app.myapp.create_rectangle(lt_cab_width, 0,
                                   30, 10,
                                   "white", ("background", "topmost"))       # stove back

    def dining():
        print("Adding dining background")
        grout_bg(fraction("90.1/16"), fraction("17.1/2"))
        app.myapp.create_rectangle(0, fraction("17.1/2"),
                                   fraction("25.5/8"), fraction("36.3/4"),
                                   cabinet, ("background", "topmost"))       # left cab
        rt_cab_width = fraction("25.3/8")
        app.myapp.create_rectangle(bg_width-rt_cab_width, fraction("17.1/2"),
                                   rt_cab_width, fraction("36.11/16"),
                                   cabinet, ("background", "topmost"))       # right cab

    app.init((("Choose Color", choose_color),
             #("Dialog Test", run_dialog),
              ("Sink Background", sink), ("Stove Background", stove),
              ("Dining Background", dining),
              ("Set Grout Color", run_set_grout_color),
              ("Hopscotch", run_hop), ("Herringbone", run_herr), ("Stepped", run_step)))

    app.run()

