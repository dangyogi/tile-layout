# app.py

from tkinter import *
from tkinter.ttk import *


class App(Frame):
    def __init__(self, master, test=False):
        super().__init__(master)
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        #self.master = master
        fix(self)
        self.scale = 10  # pixels/tile-inch
        self.create_widgets(test)

    def in_to_px(self, in_):
        return float(in_) * self.scale

    def create_widgets(self, test):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas = MyCanvas(self, bg="#777")
        fix(self.canvas, 0, 0)
        print(f"{self.canvas['width']=}, {self.canvas['height']=}") 
        print(f"{self.canvas.winfo_reqwidth()=}, {self.canvas.winfo_reqheight()=}") 
        if test:
            self.create_rectangle(20, 10, 10, 4, "black")
            self.create_rectangle(30.25, 12, 2, 2, "yellow")

    def create_rectangle(self, left, bottom, width, height, color, tags=()):
        r'''Parameters are in inches.
        '''
        return self.canvas.create_my_rectangle(
                             (self.in_to_px(left), self.in_to_px(bottom)),
                             self.in_to_px(width), self.in_to_px(height),
                             color,
                             tags)

    def create_polygon(self, color, *points, tags=()):
        r'''Points are in inches.
        '''
        return self.canvas.create_my_polygon(
                 color,
                 *((self.in_to_px(x), self.in_to_px(y)) for x, y in points),
                 tags=tags)

    def canvas_size(self):
        return self.canvas.size()

    def scale_width(self, inches):
        width, height = self.canvas_size()
        self.scale = width / float(inches)
        print(f"new size in inches: {width / self.scale} W x {height / self.scale} H")


class MyCanvas(Canvas):
    def __init__(self, parent, **kwargs):
        Canvas.__init__(self, parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.width = self.winfo_reqwidth() - 2     # pixels
        self.height = self.winfo_reqheight() - 2   # pixels
        print(f"MyCanvas.__init__: {self.size()=}")

    def on_resize(self, event):
        dheight = event.height - self.height
        print(f"{event.height=}, {self.height=}, {dheight=}")
        self.width = event.width
        self.height = event.height
        self.config(width=event.width, height=event.height)
        print(f"on_resize: ({event.width=}, {event.height=}, "
              f"({self.winfo_reqwidth()=}, {self.winfo_reqheight()=}")
        #self.move("math", 0, dheight)

    def create_my_rectangle(self, ll_corner, width, height, color, tags=()):
        return self.create_rectangle(
                      self.math_coord(ll_corner),
                      self.math_coord((ll_corner[0] + width, ll_corner[1] + height)),
                      width=0, fill=color, tags=tags + ("math",))

    def create_my_polygon(self, color, *points, tags=()):
        return self.create_polygon(*(self.math_coord(pt) for pt in points),
                                   width=0, fill=color, tags=tags + ("math",))

    def create_my_circle(self, color, pos, diameter, tags=()):
        return self.create_circle(self.math_coord(pos), diameter=diameter,
                                  width=0, fill=color, tags=tags + ("math",))

    def size(self):
        r'''Returns width, height in pixels.
        '''
        return self.width, self.height

    def math_coord(self, point):
        r'''Flips Y coord from video coord to math coord.

        So that 0 is at the bottom and it grows up.
        '''
        return point[0], self.height - point[1]


def size(thing):
    return thing['width'], thing['height']

def fix(thing, row=None, col=None, **kwargs):
    #thing.pack(expand=True, fill="both")
    if row is not None:
        kwargs['row'] = row
    if col is not None:
        kwargs['column'] = col
    thing.grid(sticky=N+S+E+W, **kwargs)
    #print(thing, size(thing), thing.grid_size())


def spew():
    print("Spewing:")
    print(f"Screen: width {root.winfo_screenwidth()}, height {root.winfo_screenheight()}")
    print(f"root width {root.winfo_width()}, height {root.winfo_height()}")
    print(f"{myapp.canvas.cget('background')=}")
    #print(f'{myapp.canvas.width=}, {myapp.canvas.height=}')
    print(f'{myapp.canvas_size()=}, {myapp.canvas_size()[0] / myapp.scale} W x '
          f'{myapp.canvas_size()[1] / myapp.scale} H')
    print("Done Spewing!")


def init(menus=(), test=False):
    global root, mainmenu, submenus, myapp, canvas
    root = Tk()
    root.geometry("750x250")
    mainmenu = Menu(root)
    submenus = {}
    for item in menus:
        name, *rest = item
        if not rest:
            submenu = Menu(mainmenu, tearoff=0)
            mainmenu.addcascade(label=name, menu=submenu)
            submenus[name] = submenu
        elif isinstance(rest[0], (tuple, list)):
            submenu = Menu(mainmenu, tearoff=0)
            for subname, command in rest[0]:
                submenu.add_command(label=subname, command=command)
            mainmenu.addcascade(label=name, menu=submenu)
        else:
            mainmenu.add_command(label=name, command=rest[0])
    root.configure(menu=mainmenu)
    myapp = App(root, test)
    canvas = myapp.canvas

def run():
    myapp.mainloop()



if __name__ == "__main__":
    init(test=True)
    run()
