# walls.py

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
        self.constants = {}
        if 'constants' in specs:
            for name, exp in specs['constants'].items():
                self.constants[name] = my_eval(exp, self.constants, f"<Wall({self.name}): {name}>")
                print(f"Wall({self.name}) setting {name} to {f_to_str(self.constants[name])}")
            del specs['constants']
        self.grout = eval_pair(specs['grout'], self.constants, f"<Wall({self.name})>")
        del specs['grout']
        self.constants['width_in'], self.constants['height_in'] = self.grout

        def create_panel(name, panel):
            location = f"<Wall({self.name}) create_panel({name})>"
            pos = eval_pair(panel['pos'], self.constants, location)
            size = eval_pair(panel['size'], self.constants, location, relaxed=True)
            skip = my_eval(panel.get('skip', False), self.constants, f"<Wall({self.name}) skip>")
            print(f"Wall panel {name=}, {skip=}")
            if 'image' in panel:
                return Image_panel(name, pos, size, panel['image'], skip)
            color = eval_color(panel['color'], colors)
            if isinstance(size, tuple):
                return Rect_panel(name, pos, size, color, skip)
            return Circle_panel(name, pos, size, color, skip)

        self.panels = {name: create_panel(name, panel) for name, panel in specs.items()}

    def grout_bg(self):
        width_in, height_in = self.grout
        app.canvas.set_scale(width_in, height_in)
        app.canvas.create_my_rectangle("grout_bg", 0, 0, width_in, height_in, 'black',
                                       ("background", "grout"))
        app.canvas.current_grout_color = 'black'
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


class Panel:
    tags = "background", "topmost"

    def __init__(self, name, pos, skip):
        self.name = name
        self.pos = pos
        self.skip = skip


class Rect_panel(Panel):
    def __init__(self, name, pos, size, color, skip):
        super().__init__(name, pos, skip)
        self.size = size
        self.color = color
        self.left = pos[0]
        self.bottom = pos[1]
        print(f"Rect_panel({self.name}): self.bottom={f_to_str(self.bottom)}")
        self.right = self.left + size[0]
        self.top = self.bottom + size[1]

    def __str__(self):
        return f"<Rect_panel({self.name}), pos: {f_to_str(self.pos)}, " \
               f"size: {f_to_str(self.size)}, color: {self.color}>"

    def create(self):
        if not self.skip:
            app.canvas.create_my_rectangle("wall",
              self.pos[0], self.pos[1],
              self.size[0], self.size[1],
              self.color, self.tags)


class Circle_panel(Panel):
    def __init__(self, name, pos, diameter, color, skip):
        super().__init__(name, pos, skip)
        self.diameter = diameter
        self.color = color
        self.bottom = pos[1] - diameter / 2
        self.top = self.bottom + diameter
        self.left = pos[0] - diameter / 2
        self.right = self.left + diameter

    def __str__(self):
        return f"<Circle_panel({self.name}), pos: {f_to_str(self.pos)}, " \
               f"diameter: {f_to_str(self.diameter)}, color: {self.color}>"

    def create(self):
        if not self.skip:
            app.canvas.create_my_circle("wall", self.color, self.pos, self.diameter,
                                        self.tags)


class Image_panel(Panel):
    def __init__(self, name, pos, size, image, skip):
        super().__init__(name, pos, skip)
        self.size = size
        self.image_file = image
        self.image = Image.open(os.path.join('images', self.image_file))
        self.scale = None
        self.left = pos[0]
        self.bottom = pos[1]
        self.right = self.left + size[0]
        self.top = self.bottom + size[1]

    def __str__(self):
        return f"<Image_panel({self.name}), pos: {f_to_str(self.pos)}, " \
               f"size: {f_to_str(self.size)}, image: {self.image_file}>"

    def create(self):
        if not self.skip:
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
