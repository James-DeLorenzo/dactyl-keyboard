import solid as sl
from subprocess import run
import logging

logger = logging.getLogger()

class HelperSolid():
    
    def box(self, width, height, depth):
        return sl.cube([width, height, depth], center=True)


    def cylinder(self, radius, height, segments=100):
        return sl.cylinder(r=radius, h=height, segments=segments, center=True)


    def sphere(self, radius):
        return sl.sphere(radius)


    def cone(self, r1, r2, height):
        return sl.cylinder(r1=r1, r2=r2, h=height)  # , center=True)


    def rotate(self, shape, angle):
        return sl.rotate(angle)(shape)


    def translate(self, shape, vector):
        return sl.translate(tuple(vector))(shape)


    def mirror(self, shape, plane=None):
        logger.debug('mirror()')
        planes = {
            'XY': [0, 0, 1],
            'YX': [0, 0, -1],
            'XZ': [0, 1, 0],
            'ZX': [0, -1, 0],
            'YZ': [1, 0, 0],
            'ZY': [-1, 0, 0],
        }
        return sl.mirror(planes[plane])(shape)


    def union(self, shapes):
        logger.debug('union()')
        shape = None
        for item in shapes:
            if shape is None:
                shape = item
            else:
                shape += item
        return shape


    def add(self, shapes):
        logger.debug('union()')
        shape = None
        for item in shapes:
            if shape is None:
                shape = item
            else:
                shape += item
        return shape


    def difference(self, shape, shapes):
        logger.debug('difference()')
        for item in shapes:
            shape -= item
        return shape


    def intersect(self, shape1, shape2):
        return sl.intersection()(shape1, shape2)


    def hull_from_points(self, points):
        return sl.hull()(*points)


    def hull_from_shapes(self, shapes, points=None):
        hs = []
        if points is not None:
            hs.extend(points)
        if shapes is not None:
            hs.extend(shapes)
        return sl.hull()(*hs)


    def tess_hull(self, shapes, sl_tol=.5, sl_angTol=1):
        return sl.hull()(*shapes)


    def triangle_hulls(self, shapes):
        logger.debug('triangle_hulls()')
        hulls = []
        for i in range(len(shapes) - 2):
            hulls.append(self.hull_from_shapes(shapes[i: (i + 3)]))

        return self.union(hulls)



    def bottom_hull(self, p, height=0.001):
        logger.debug("bottom_hull()")
        shape = None
        for item in p:
            proj = sl.projection()(p)
            t_shape = sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(
                proj
            )
            t_shape = sl.translate([0, 0, height / 2 - 10])(t_shape)
            if shape is None:
                shape = t_shape
            shape = sl.hull()(p, shape, t_shape)
        return shape

    def polyline(self, point_list):
        return sl.polygon(point_list)


    # def project_to_plate(self, ):
    #     square = cq.Workplane('XY').rect(1000, 1000)
    #     for wire in square.wires().objects:
    #         plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))

    def extrude_poly(self, outer_poly, inner_polys=None, height=1):
        if inner_polys is not None:
            return sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(outer_poly, *inner_polys)
        else:
            return sl.linear_extrude(height=height, twist=0, convexity=0, center=True)(outer_poly)


    def import_file(self, fname, convexity=4):
        full_name = fname + r".stl"
        logger.info("IMPORTING FROM {}".format(full_name))

        return sl.import_stl(full_name, convexity=convexity)


    def export_file(self, shape, fname):
        logger.info("EXPORTING TO {}".format(fname))
        sl.scad_render_to_file(shape, fname + ".scad")

    def export_stl(self, shape, fname):
        logger.info("EXPORTING STL TO {}".format(fname))
        run(["C:\\Program Files\\OpenSCAD\\openscad.com", "-o",  f"{fname}_openscad.stl", f"{fname}.scad"]) # TODO: make this portable across platforms


    def export_dxf(self, shape, fname):
        logger.info("NO DXF EXPORT FOR SOLID".format(fname))
        pass
