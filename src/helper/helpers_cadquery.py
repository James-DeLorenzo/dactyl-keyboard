import cadquery as cq
from scipy.spatial import ConvexHull as sphull
import numpy as np
import logging

logger = logging.getLogger()

class HelperCadquery():

    debug_trace = False

    def __init__(self): pass

    def box(self, width, height, depth):
        return cq.Workplane("XY").box(width, height, depth)


    def cylinder(self, radius, height, segments=100):
        shape = cq.Workplane("XY").union(cq.Solid.makeCylinder(radius=radius, height=height))
        shape = self.translate(shape, (0, 0, -height/2))
        return shape


    def sphere(self, radius):
        return cq.Workplane('XY').union(cq.Solid.makeSphere(radius))


    def cone(self, r1, r2, height):
        return cq.Workplane('XY').union(
            cq.Solid.makeCone(radius1=r1, radius2=r2, height=height))


    def rotate(self, shape, angle):
        origin = (0, 0, 0)
        shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(1, 0, 0), angleDegrees=angle[0])
        shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(0, 1, 0), angleDegrees=angle[1])
        shape = shape.rotate(axisStartPoint=origin, axisEndPoint=(0, 0, 1), angleDegrees=angle[2])
        return shape


    def translate(self, shape, vector):
        return shape.translate(tuple(vector))


    def mirror(self, shape, plane=None):
        logger.debug('mirror()')
        return shape.mirror(mirrorPlane=plane)


    def union(self, shapes):
        logger.debug('union()')
        shape = None
        for item in shapes:
            if shape is None:
                shape = item
            else:
                shape = shape.union(item)
        return shape


    def add(self, shapes):
        logger.debug('union()')
        shape = None
        for item in shapes:
            if shape is None:
                shape = item
            else:
                shape = shape.add(item)
        return shape


    def difference(self, shape, shapes):
        logger.debug('difference()')
        for item in shapes:
            shape = shape.cut(item)
        return shape


    def intersect(self, shape1, shape2):
        return shape1.intersect(shape2)


    def face_from_points(self, points):
        # logger.debug('face_from_points()')
        edges = []
        num_pnts = len(points)
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % num_pnts]
            edges.append(
                cq.Edge.makeLine(
                    cq.Vector(p1[0], p1[1], p1[2]),
                    cq.Vector(p2[0], p2[1], p2[2]),
                )
            )

        face = cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))

        return face


    def hull_from_points(self, points):
        # logger.debug('hull_from_points()')
        hull_calc = sphull(points)
        n_faces = len(hull_calc.simplices)

        faces = []
        for i in range(n_faces):
            face_items = hull_calc.simplices[i]
            fpnts = []
            for item in face_items:
                fpnts.append(points[item])
            faces.append(self.face_from_points(fpnts))

        shape = cq.Solid.makeSolid(cq.Shell.makeShell(faces))
        shape = cq.Workplane('XY').union(shape)
        return shape


    def hull_from_shapes(self, shapes, points=None):
        # logger.debug('hull_from_shapes()')
        vertices = []
        for shape in shapes:
            verts = shape.vertices()
            for vert in verts.objects:
                vertices.append(np.array(vert.toTuple()))
        if points is not None:
            for point in points:
                vertices.append(np.array(point))

        shape = self.hull_from_points(vertices)
        return shape


    def tess_hull(self, shapes, sl_tol=.5, sl_angTol=1):
        # logger.debug('hull_from_shapes()')
        vertices = []
        solids = []
        for wp in shapes:
            for item in wp.solids().objects:
                solids.append(item)

        for shape in solids:
            verts = shape.tessellate(sl_tol, sl_angTol)[0]
            for vert in verts:
                vertices.append(np.array(vert.toTuple()))

        shape = self.hull_from_points(vertices)
        return shape


    def triangle_hulls(self, shapes):
        logger.debug('triangle_hulls()')
        hulls = [cq.Workplane('XY')]
        for i in range(len(shapes) - 2):
            hulls.append(self.hull_from_shapes(shapes[i: (i + 3)]))

        return self.union(hulls)


    def bottom_hull(self, p, height=0.001):
        logger.debug("bottom_hull()")
        shape = None
        for item in p:
            vertices = []
            # verts = item.faces('<Z').vertices()
            verts = item.faces().vertices()
            for vert in verts.objects:
                v0 = vert.toTuple()
                v1 = [v0[0], v0[1], -10]
                vertices.append(np.array(v0))
                vertices.append(np.array(v1))

            t_shape = self.hull_from_points(vertices)

            # t_shape = translate(t_shape, [0, 0, height / 2 - 10])

            if shape is None:
                shape = t_shape

            for shp in (*p, shape, t_shape):
                try:
                    shp.vertices()
                except:
                    0
            shape = self.union([shape, self.hull_from_shapes((shape, t_shape))])

        return shape


    def polyline(self, point_list):
        return cq.Workplane('XY').polyline(point_list)


    # def project_to_plate(self, ):
    #     square = cq.Workplane('XY').rect(1000, 1000)
    #     for wire in square.wires().objects:
    #         plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))


    def extrude_poly(self, outer_poly, inner_polys=None, height=1):  # vector=(0,0,1)):
        outer_wires = cq.Wire.assembleEdges(outer_poly.edges().objects)
        inner_wires = []
        if inner_polys is not None:
            for item in inner_polys:
                inner_wires.append(cq.Wire.assembleEdges(item.edges().objects))

        return cq.Workplane('XY').add(
            cq.Solid.extrudeLinear(outerWire=outer_wires, innerWires=inner_wires, vecNormal=cq.Vector(0, 0, height)))


    def import_file(self, fname, convexity=None):
        logger.info("IMPORTING FROM {}".format(fname))
        return cq.Workplane('XY').add(cq.importers.importShape(
            cq.exporters.ExportTypes.STEP,
            fname + ".step"))

    def export_stl(self, shape, fname):
        logger.info("EXPORTING STL TO {}".format(fname))
        cq.exporters.export(shape, fname=fname + "_cadquery.stl", exportType="STL")

    def export_file(self, shape, fname):
        logger.info("EXPORTING TO {}".format(fname))
        cq.exporters.export(w=shape, fname=fname + ".step",
                            exportType='STEP')

        self.export_stl(shape, fname)


    def export_dxf(self, shape, fname):
        logger.info("EXPORTING TO {}".format(fname))
        cq.exporters.export(w=shape, fname=fname + ".dxf",
                            exportType='DXF')

    def blockerize(self, shape):
        #####
        # Inputs
        ######
        lbumps = 40  # number of bumps long
        wbumps = 40  # number of bumps wide
        thin = True  # True for thin, False for thick

        #
        # Lego Brick Constants-- these make a Lego brick a Lego :)
        #
        pitch = 8.0
        clearance = 1
        bumpDiam = 4.85
        bumpHeight = 1.8
        if thin:
            height = 3.2
        else:
            height = 9.6

        t = (pitch - (2 * clearance) - bumpDiam) / 2.0
        postDiam = 6.5  # pitch  t  # works out to 6.5
        total_length = lbumps * pitch - 2.0 * clearance
        total_width = wbumps * pitch - 2.0 * clearance

        # make the base
        # s = cq.Workplane("XY").box(total_length, total_width, height)

        # shell inwards not outwards
        s = shape.faces("<Z").shell(-2.5 * t)

        # make the bumps on the top
        s = (s.faces(">Z").workplane().
             rarray(pitch, pitch, lbumps, wbumps, True).circle(bumpDiam / 2.0)
             .extrude(bumpHeight))

        # add posts on the bottom. posts are different diameter depending on geometry
        # solid studs for 1 bump, tubes for multiple, none for 1x1
        tmp = s.faces("<Z").workplane(invert=True)

        if lbumps > 1 and wbumps > 1:
            tmp = (tmp.rarray(pitch, pitch, lbumps - 1, wbumps - 1, center=True).
                   circle(postDiam / 2.0).circle(bumpDiam / 2.0).extrude(height - t))
        elif lbumps > 1:
            tmp = (tmp.rarray(pitch, pitch, lbumps - 1, 1, center=True).
                   circle(t).extrude(height - t))
        elif wbumps > 1:
            tmp = (tmp.rarray(pitch, pitch, 1, wbumps - 1, center=True).
                   circle(t).extrude(height - t))
        else:
            tmp = s

        return self.intersect(shape, tmp)

    # generate a cutter to exact size/shape of an M3 4mm x 4mm brass insert
    # size is scaled a bit for non-resin prints, so heat-set works
    def insert_cutter(self, radii=(2.35, 2.0), heights=(2.8, 1.5), scale_by=1):
        if len(radii) != len(heights):
            raise Exception("radii and heights collections must have equal length")

        top_radius = 4.7 / 2
        top_height = 2.8
        medium_radius = 4.0 / 2
        medium_height = 1.5
        # medium2_radius = 5.1 / 2
        # medium2_height = 0.8
        # bottom_radius = 4.85 / 2
        # bottom_height = 1.6

        total_height = sum(heights) + 0.3  # add 0.3 for a titch extra

        half_height = total_height / 2
        offset = half_height
        cyl = None
        for i in range(len(radii)):
            radius = radii[i] * scale_by
            height = heights[i]
            offset -= height / 2
            new_cyl = cq.Workplane('XY').cylinder(height, radius).translate((0, 0, offset))
            if cyl is None:
                cyl = new_cyl
            else:
                cyl = cyl.union(new_cyl)
            offset -= height / 2

        return cyl
