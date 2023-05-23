# alignment.py

from math import sin, cos, radians


class Alignment:
    r'''Applies a rotation and translation to a point.

    The rotation angle is in degrees, positive is counterclockwise.

    The offsets are applied after the rotation.
    '''
    attrs = 'angle,x_offset,y_offset'.split(',')

    def __init__(self, alignment):
        for attr in self.attrs:
            setattr(self, attr, alignment[attr])
        self.radians = radians(self.angle)

    def dump(self):
        return {attr: getattr(self, attr) for attr in self.attrs}

    def rotate(self, pt):
        s, c = sin(self.radians), cos(self.radians)
        x, y = pt
        return x * c - y * s, x * s + y * c

    def align_pt(self, pt):
        x, y = self.rotate(pt)
        return x + self.x_offset, y + self.y_offset

    def align(self, pts):
        return [self.align_pt(p) for p in pts]
