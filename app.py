# app.py

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


class MyCanvas(Canvas):
    def __init__(self, parent, **kwargs):
        Canvas.__init__(self, parent, **kwargs)
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

    def set_scale(self):
        width, height = self.size()
        self.my_scale = min(width / float(myapp.bg_width), height / float(myapp.bg_height))
        print(f"new size in inches: {self.px_to_in(width)} W x {self.px_to_in(height)} H")

    def create_my_rectangle(self, caller, left_x, bottom_y, width, height, color, tags=()):
        #print(f"create_my_rectangle({caller=}, left_x={f_to_str(left_x)}, "
        #      f"bottom_y={f_to_str(bottom_y)}, width={f_to_str(width)}, "
        #      f"height={f_to_str(height)})")
        #print(f"create_rectangle({f_to_str(self.math_coord((left_x, bottom_y)))}, "
        #              f"{f_to_str(self.math_coord((left_x + width, bottom_y + height)))}")
        return self.create_rectangle(
                      self.math_coord((left_x, bottom_y)),
                      self.math_coord((left_x + width, bottom_y + height)),
                      width=0, fill=color, tags=tags + ("math",))

    def create_my_polygon(self, caller, color, *points, tags=()):
        #print(f"create_my_polygon({caller=}, points={f_to_str(points)})")
        start_x = max(0, points[0][0])
        end_x = min(myapp.bg_width, points[1][0])
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

    def size(self):
        r'''Returns width, height in pixels.
        '''
        return self.my_width, self.my_height

    def math_coord(self, point):
        r'''Flips Y coord from video coord to math coord.

        So that 0 is at the bottom and it grows up.
        '''
        return self.in_to_px(point[0]), self.my_height - self.in_to_px(point[1])


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
    print(f"{myapp.submenus['Pattern'].index('end')=}")
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
