# walls.py

from math import hypot
import os.path
from PIL import Image, ImageTk

import app
from utils import read_yaml, my_eval, eval_pair, eval_color, f_to_str


def read_walls(colors=None, filename='walls.yaml'):
    return {name: Wall(name, specs, colors)
            for name, specs in read_yaml(filename).items()}


class Wall:
    def __init__(self, name, specs, colors):
        self.name = name
        constants = {}
        if 'constants' in specs:
            for name, exp in specs['constants'].items():
                constants[name] = my_eval(exp, constants, f"<Wall({self.name}): {name}>")
            del specs['constants']
        self.grout = eval_pair(specs['grout'], constants, f"<Wall({self.name})>")
        del specs['grout']
        constants['width_in'], constants['height_in'] = self.grout
        self.max_x = max_x = self.grout[0]
        self.max_y = max_y = self.grout[1]
        self.diagonal = hypot(max_x, max_y)
        self.boundary = (0, 0), (max_x, 0), (max_x, max_y), (0, max_y)
        if self.name == "Master Back":
            print(f"Wall({self.name}) boundary={f_to_str(self.boundary)}")

        def create_panel(name, panel):
            location = f"<Wall({self.name}) create_panel({name})>"
            pos = eval_pair(panel['pos'], constants, location)
            size = eval_pair(panel['size'], constants, location, relaxed=True)
            if 'image' in panel:
                return Image_panel(name, pos, size, panel['image'])
            color = eval_color(panel['color'], colors)
            if isinstance(size, tuple):
                return Rect_panel(name, pos, size, color)
            return Circle_panel(name, pos, size, color)

        self.panels = {name: create_panel(name, panel) for name, panel in specs.items()}

    def grout_bg(self):
        width_in, height_in = app.canvas.width_in, app.canvas.height_in = self.grout
        app.canvas.set_scale()
        app.canvas.create_my_rectangle("grout_bg", 0, 0, width_in, height_in, 'black',
                                       ("background", "grout"))
        bg_color = app.canvas.cget('background')

        # clip above grout background, across entire canvas
        if app.canvas.my_height > app.canvas.in_to_px(height_in):
            app.canvas.create_my_rectangle(
              "grout clip above", 0, height_in,
              app.canvas.px_to_in(app.canvas.my_width),
              app.canvas.px_to_in(app.canvas.my_height) - height_in,
              bg_color, ("background", "topmost"))

        # clip to the right of grout background
        if app.canvas.my_width > app.canvas.in_to_px(width_in):
            app.canvas.create_my_rectangle(
              "grout clip right", width_in, 0,
              app.canvas.px_to_in(app.canvas.my_width) - width_in, height_in,
              bg_color, ("background", "topmost"))

    def create(self):
        app.canvas.delete("all")
        self.grout_bg()
        for p in self.panels.values():
            p.create()

    def visible(self, points):
        r'''True if there are points to the right of 0, left of max_x, above 0, and below max_y.

        These don't have to be the same point.  For example one point might be x < 0, which counts
        for left of max_x, but not right of 0.  Another point might be > max_x, which counts the
        other way.
        '''
        to_right = to_left = to_top = to_bottom = False
        for x, y in points:
            if x > 0: to_right = True
            if x < self.max_x: to_left = True
            if y > 0: to_top = True
            if y < self.max_y: to_bottom = True
        return all((to_left, to_right, to_top, to_bottom))



class Panel:
    tags = "background", "topmost"

    def __init__(self, name, pos):
        self.name = name
        self.pos = pos


class Rect_panel(Panel):
    def __init__(self, name, pos, size, color):
        super().__init__(name, pos)
        self.size = size
        self.color = color

    def __str__(self):
        return f"<Rect_panel({self.name}), pos: {f_to_str(self.pos)}, " \
               f"size: {f_to_str(self.size)}, color: {self.color}>"

    def create(self):
        app.canvas.create_my_rectangle("wall",
          self.pos[0], self.pos[1],
          self.size[0], self.size[1],
          self.color, self.tags)


class Circle_panel(Panel):
    def __init__(self, name, pos, diameter, color):
        super().__init__(name, pos)
        self.diameter = diameter
        self.color = color

    def __str__(self):
        return f"<Circle_panel({self.name}), pos: {f_to_str(self.pos)}, " \
               f"diameter: {f_to_str(self.diameter)}, color: {self.color}>"

    def create(self):
        app.canvas.create_my_circle("wall", self.color, self.pos, self.diameter, self.tags)


class Image_panel(Panel):
    def __init__(self, name, pos, size, image):
        super().__init__(name, pos)
        self.size = size
        self.image_file = image
        self.image = Image.open(os.path.join('images', self.image_file))
        self.scale = None

    def __str__(self):
        return f"<Image_panel({self.name}), pos: {f_to_str(self.pos)}, " \
               f"size: {f_to_str(self.size)}, image: {self.image_file}>"

    def create(self):
        if app.canvas.my_scale != self.scale:
            px_width = app.canvas.in_to_px(self.size[0])
            px_height = app.canvas.in_to_px(self.size[1])
            self.scaled_image = ImageTk.PhotoImage(
                                  self.image.resize((int(round(px_width)),
                                                     int(round(px_height)))))
            self.scale = app.canvas.my_scale
        app.canvas.create_my_image("wall", self.scaled_image, (0, 0), self.pos, self.tags)



if __name__ == "__main__":
    from pprint import pp

    def dump(name, wall):
        print(name)
        print("  name:", wall.name)
        print("  grout:", f_to_str(wall.grout))
        print("  panels:")
        for p_name, panel in wall.panels.items():
            print(f"    {p_name}: {panel}")
        print()

    for name, wall in read_walls(dict(cabinet='#123')).items():
        dump(name, wall)
