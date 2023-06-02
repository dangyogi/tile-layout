# app.py

from math import hypot
from tkinter import *
from tkinter.ttk import *

from utils import f_to_str


class App(Frame):
    def __init__(self, master, test=False):
        super().__init__(master)
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        #self.master = master
        fix(self)
        self.create_widgets(test)

    def create_widgets(self, test):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = MyCanvas(self, bg="#777")
        fix(self.canvas, 0, 0)
        print(f"{self.canvas.size()=}")
        print(f"{self.canvas.winfo_reqwidth()=}, {self.canvas.winfo_reqheight()=}") 
        if test:
            if False:
                self.canvas.create_rectangle((200.0, 100.0), (300.0, 60.0),
                                             fill="black", width=0, tags=("math",))
                self.canvas.create_rectangle((302.5, 120.0), (322.5, 100.0),
                                             fill="yellow", width=0)
            else:
                self.canvas.create_my_rectangle("test black", 20, 10, 10, 4, "black")
                self.canvas.create_my_rectangle("test yellow", 30.25, 12, 2, 2, "yellow")


class MyCanvasBase(Canvas):
    def create_my_rectangle(self, caller, left_x, bottom_y, width, height, color,
                            tags=()):
        #print(f"create_my_rectangle({caller=}, left_x={f_to_str(left_x)}, "
        #      f"bottom_y={f_to_str(bottom_y)}, width={f_to_str(width)}, "
        #      f"height={f_to_str(height)})")
        #print(f"create_rectangle({f_to_str(self.math_coord((left_x, bottom_y)))}, "
        #      f"{f_to_str(self.math_coord((left_x + width, bottom_y + height)))}")
        return self.create_rectangle(
                      self.math_coord((left_x, bottom_y)),
                      self.math_coord((left_x + width, bottom_y + height)),
                      width=0, fill=color, tags=tags + ("math",))

    def create_my_polygon(self, caller, color, *points, tags=()):
        #print(f"create_my_polygon({caller=}, points={f_to_str(points)})")
        #start_x = max(0, points[0][0])
        #end_x = min(self.width_in, points[1][0])
        #print(f"row {points[0][1]}: length of next tile in row {end_x - start_x}")
        return self.create_polygon(*(self.math_coord(pt) for pt in points),
                                   width=0, fill=color, tags=tags + ("math",))

    def create_my_circle(self, caller, color, pos, diameter, tags=()):
        #print(f"create_my_circle({caller=}, pos={f_to_str(pos)}, "
        #      f"diameter={f_to_str(diameter)})")
        x, y = self.math_coord(pos)
        r = self.in_to_px(diameter / 2)
        return self.create_oval(x - r, y - r, x + r, y + r,
                                width=0, fill=color, tags=tags + ("math",))

    def create_my_image(self, caller, image, sw_offset, pos, tags=()):
        #print(f"create_my_image({caller=}, pos={f_to_str(pos)}, "
        #      f"diameter={f_to_str(diameter)})")
        x, y = self.math_coord((pos[0] - sw_offset[0], pos[1] - sw_offset[1]))
        return self.create_image(x, y, anchor=SW,
                                 image=image, tags=tags + ("math",))

    def create_canvas(self, caller, pos, size, tags=()):
        new_canvas = MyNestedCanvas(self, size)
        self.create_window(self.in_to_px(pos[0]), self.in_to_px(pos[1]), anchor=SW,
                           window=new_canvas, tags=tags)
        return new_canvas

    def visible(self, points):
        r'''True if there are points to the right of 0, left of width_in,
        above 0, and below height_in.

        These don't have to be the same point.  For example one point might be x < 0,
	which counts for left of width_in, but not right of 0.  Another point might
        be > width_in, which counts the other way.
        '''
        to_right = to_left = to_top = to_bottom = False
        for x, y in points:
            if x > 0: to_right = True
            if x < self.width_in: to_left = True
            if y > 0: to_top = True
            if y < self.height_in: to_bottom = True
        return all((to_left, to_right, to_top, to_bottom))


class MyCanvas(MyCanvasBase):
    def __init__(self, parent, **kwargs):
        MyCanvasBase.__init__(self, parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.my_width = self.winfo_reqwidth() - 2     # pixels
        self.my_height = self.winfo_reqheight() - 2   # pixels
        self.my_scale = 10  # pixels/tile-inch
        print(f"MyCanvas.__init__: {self.size()=}")

    def on_resize(self, event):
        dheight = event.height - self.my_height
        print(f"{event.height=}, {self.my_height=}, {dheight=}")
        self.my_width = event.width
        self.my_height = event.height
        self.config(width=event.width, height=event.height)
        print(f"on_resize: ({event.width=}, {event.height=}, "
              f"({self.winfo_reqwidth()=}, {self.winfo_reqheight()=}")
        #self.move("math", 0, dheight)

    def in_to_px(self, in_):
        return float(in_) * self.my_scale

    def px_to_in(self, px):
        return px / self.my_scale

    def set_scale(self, width_in, height_in):
        self.width_in = width_in
        self.height_in = height_in
        self.diagonal = hypot(width_in, height_in)
        self.boundary = (0, 0), (width_in, 0), (width_in, height_in), (0, height_in)
        width, height = self.size()
        self.my_scale = min(width / float(self.width_in),
                            height / float(self.height_in))
        print(f"new size in inches: "
              f"{self.px_to_in(width):.3f} W x {self.px_to_in(height):.3f} H")

    def size(self):
        r'''Returns width, height in pixels.
        '''
        return self.my_width, self.my_height

    def math_coord(self, point):
        r'''Flips Y coord from video coord to math coord.

        So that 0 is at the bottom and it grows up.

        Also converts from inches to pixels.
        '''
        return self.in_to_px(point[0]), self.my_height - self.in_to_px(point[1])


class MyNestedCanvas(MyCanvasBase):
    def __init__(self, parent, size, **kwargs):
        MyCanvasBase.__init__(self, parent,
                              width=parent.in_to_px(size[0]),
                              height=parent.in_to_px(size[1]),
                              **kwargs)
        self.parent = parent
        width_in, height_in = size
        self.width_in = width_in
        self.height_in = height_in
        self.diagonal = hypot(self.width_in, self.height_in)
        self.boundary = (0, 0), (width_in, 0), (width_in, height_in), (0, height_in)
        print(f"MyNestedCanvas, {self.parent=}, {size=}")

    def in_to_px(self, in_):
        return self.parent.in_to_px(in_)

    def px_to_in(self, px):
        return self.parent.px_to_in(px)

    def math_coord(self, point):
        r'''Flips Y coord from video coord to math coord.

        So that 0 is at the bottom and it grows up.

        Also converts from inches to pixels.
        '''
        return self.in_to_px(point[0]), self.in_to_px(self.height_in - point[1])


def fix(thing, row=None, col=None, **kwargs):
    #thing.pack(expand=True, fill="both")
    if row is not None:
        kwargs['row'] = row
    if col is not None:
        kwargs['column'] = col
    thing.grid(sticky=N+S+E+W, **kwargs)
    #print(thing, thing.grid_size())


def spew():
    print("Spewing:")
    print(f"Screen: width {root.winfo_screenwidth()}, height {root.winfo_screenheight()}")
    print(f"root width {root.winfo_width()}, height {root.winfo_height()}")
    print(f"{myapp.canvas.cget('background')=}")
    #print(f'{myapp.canvas.my_width=}, {myapp.canvas.my_height=}')
    print(f'{canvas.size()=}, {canvas.px_to_in(canvas.size()[0]):.3f} W x '
          f'{canvas.px_to_in(canvas.size()[1]):.3f} H')
    #print(f"{dir(myapp.submenus['Wall'])=}")
    print(f"{myapp.submenus['Wall'].index('end')=}")
    print(f"{myapp.submenus['Plans'].index('end')=}")
    print(f"Colors: {sorted(Colors.keys())}")
    print(f"Shapes: {sorted(Shapes.keys())}")
    print(f"Tiles: {sorted(Tiles.keys())}")
    print(f"Layouts: {sorted(Layouts.keys())}")
    print(f"Walls: {sorted(Walls.keys())}")
    print("Done Spewing!")


def init(menus=(), test=False):
    global root, myapp, canvas
    root = Tk()
    root.geometry("750x250")
    mainmenu = Menu(root)
    submenus = {}
    for item in menus:
        name, *rest = item
        if not rest:
            submenu = Menu(mainmenu, tearoff=0)
            mainmenu.add_cascade(label=name, menu=submenu)
            submenus[name] = submenu
        elif isinstance(rest[0], (tuple, list)):
            submenu = Menu(mainmenu, tearoff=0)
            for subname, command in rest[0]:
                submenu.add_command(label=subname, command=command)
            mainmenu.add_cascade(label=name, menu=submenu)
        else:
            mainmenu.add_command(label=name, command=rest[0])
    root.configure(menu=mainmenu)
    myapp = App(root, test)
    myapp.mainmenu = mainmenu
    myapp.submenus = submenus
    canvas = myapp.canvas

def run():
    myapp.mainloop()



if __name__ == "__main__":
    init(test=True)
    run()
