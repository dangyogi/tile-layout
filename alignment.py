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

    def unrotate(self, pt):
        s, c = sin(-self.radians), cos(-self.radians)
        x, y = pt
        return x * c - y * s, x * s + y * c

    def unalign_pt(self, pt):
        pt2 = pt[0] - self.x_offset, pt[1] - self.y_offset
        return self.unrotate(pt2)



if __name__ == "__main__":
    a = Alignment(dict(angle=20, x_offset=2, y_offset=4))
    for pt in (0, 0), (10, 3), (-10, 3), (10, -3), (-10, -3):
        apt = a.align_pt(pt)
        pt2 = a.unalign_pt(apt)
        print(f"First pass: {pt=} -> apt=({apt[0]:.3f}, {apt[1]:.3f}) -> pt2=({pt2[0]:.3f}, {pt2[1]:.3f})")

    a = Alignment(dict(angle=0, x_offset=0, y_offset=0))
    for pt in (0, 0), (10, 3), (-10, 3), (10, -3), (-10, -3):
        apt = a.align_pt(pt)
        pt2 = a.unalign_pt(apt)
        print(f"Second pass: {pt=} -> apt=({apt[0]:.3f}, {apt[1]:.3f}) -> pt2=({pt2[0]:.3f}, {pt2[1]:.3f})")

