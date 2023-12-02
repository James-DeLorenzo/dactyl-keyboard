from clusters.trackball_orbyl import TrackballOrbyl
import math
import json
import os
import logging
import numpy as np
from utils import plate

logger = logging.getLogger()

class TrackballCJ(TrackballOrbyl):
    tbcj_inner_diameter = 42
    tbcj_thickness = 2
    tbcj_outer_diameter = 53
    
    name = "TRACKBALL_CJ"

    def get_config(self):
        with open(os.path.join("src", "clusters", "json", "TRACKBALL_CJ.json"), mode='r') as fid:
            data = json.load(fid)

        superdata = super().get_config()

        # overwrite any super variables with this class' needs
        for item in data:
            superdata[item] = data[item]

        for item in superdata:
            if not hasattr(self, str(item)):
                print(f"{self.name}: NO MEMBER VARIABLE FOR {str(item)}")
                continue
            setattr(self, str(item), superdata[item])

        return superdata

    def __init__(self, *args, **kwargs):
        logger.debug(args)
        logger.debug(kwargs)
        super().__init__(*args, **kwargs)
        self.super = super()

    def position_rotation(self):
        pos = np.array([-15, -60, -12]) + self.thumborigin()
        rot = (0, 0, 0)
        return pos, rot

    @staticmethod
    def oct_corner(helper, i, diameter, shape):
        radius = diameter / 2
        i = (i + 1) % 8

        r = radius
        m = radius * math.tan(math.pi / 8)

        points_x = [m, r, r, m, -m, -r, -r, -m]
        points_y = [r, m, -m, -r, -r, -m, m, r]

        return helper.translate(shape, (points_x[i], points_y[i], 0))

    def tr_place(self, shape):
        shape = self.helper.rotate(shape, [10, -15, 10])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-12, -16, 3])
        return shape

    def tl_place(self, shape):
        shape = self.helper.rotate(shape, [7.5, -18, 10])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-32.5, -14.5, -2.5])
        return shape

    def ml_place(self, shape):
        shape = self.helper.rotate(shape, [6, -34, 40])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-51, -25, -12])
        return shape

    def bl_place(self, shape):
        logger.debug('thumb_bl_place()')
        shape = self.helper.rotate(shape, [-4, -35, 52])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-56.3, -43.3, -23.5])
        return shape

    def track_place(self, shape):
        loc = np.array([-15, -60, -12]) + self.thumborigin()
        shape = self.helper.translate(shape, loc)
        shape = self.helper.rotate(shape, (0, 0, 0))
        return shape

    def thumb_layout(self, shape):
        return self.helper.union([
            self.tr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])),
            self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation])),
            self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
            self.bl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
        ])

    def tbcj_edge_post(self, i):
        shape = self.helper.box(self.settings["post_size"], self.settings["post_size"], self.tbcj_thickness)
        shape = self.oct_corner(self.helper, i, self.tbcj_outer_diameter, shape)
        return shape

    def tbcj_web_post(self, i):
        shape = self.helper.box(self.settings["post_size"], self.settings["post_size"], self.tbcj_thickness)
        shape = self.oct_corner(self.helper, i, self.tbcj_outer_diameter, shape)
        return shape

    def tbcj_holder(self):
        center = self.helper.box(self.settings["post_size"], self.settings["post_size"], self.tbcj_thickness)

        shape = []
        for i in range(8):
            shape_ = self.helper.hull_from_shapes([
                center,
                self.tbcj_edge_post(i),
                self.tbcj_edge_post(i + 1),
            ])
            shape.append(shape_)
        shape = self.helper.union(shape)

        shape = self.helper.difference(
            shape,
            [self.helper.cylinder(self.tbcj_inner_diameter / 2, self.tbcj_thickness + 0.1)]
        )

        return shape

    def thumb(self, side="right"):
        t = self.thumb_layout(plate.single_plate(self.settings, self.helper, side=side))
        tb = self.track_place(self.tbcj_holder())
        return self.helper.union([t, tb])

    def thumbcaps(self, side='right'):
        t = self.thumb_layout(self.capbuilder.sa_cap(1))
        return t

    def thumb_connectors(self, side="right"):
        print('thumb_connectors()')
        hulls = []

        # Top two
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_br()),
                    self.tr_place(self.connector.web_post_tl()),
                    self.tr_place(self.connector.web_post_bl()),
                ]
            )
        )

        # centers of the bottom four
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.bl_place(self.connector.web_post_tr()),
                    self.bl_place(self.connector.web_post_br()),
                    self.ml_place(self.connector.web_post_tl()),
                    self.ml_place(self.connector.web_post_bl()),
                ]
            )
        )

        # top two to the middle two, starting on the left

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl()),
                    self.ml_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_bl()),
                    self.ml_place(self.connector.web_post_br()),
                    self.tl_place(self.connector.web_post_br()),
                    self.tr_place(self.connector.web_post_bl()),
                    self.tr_place(self.connector.web_post_br()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.tl_place(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 0, self.settings["cornerrow"]),
                    self.tr_place(self.connector.web_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),
                    self.tr_place(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tr_place(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tr_place(self.connector.web_post_br()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 3, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 4, self.settings["cornerrow"]),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["cornerrow"]),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 4, self.settings["cornerrow"]),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.track_place(self.tbcj_web_post(4)),
                    self.bl_place(self.connector.web_post_bl()),
                    self.track_place(self.tbcj_web_post(5)),
                    self.bl_place(self.connector.web_post_br()),
                    self.track_place(self.tbcj_web_post(6)),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.bl_place(self.connector.web_post_br()),
                    self.track_place(self.tbcj_web_post(6)),
                    self.ml_place(self.connector.web_post_bl()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.ml_place(self.connector.web_post_bl()),
                    self.track_place(self.tbcj_web_post(6)),
                    self.ml_place(self.connector.web_post_br()),
                    self.tr_place(self.connector.web_post_bl()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.track_place(self.tbcj_web_post(6)),
                    self.tr_place(self.connector.web_post_bl()),
                    self.track_place(self.tbcj_web_post(7)),
                    self.tr_place(self.connector.web_post_br()),
                    self.track_place(self.tbcj_web_post(0)),
                    self.tr_place(self.connector.web_post_br()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                ]
            )
        )

        return self.helper.union(hulls)

    # todo update self.wallbuilder.walls for wild track, still identical to orbyl
    def walls(self, side="right"):
        print('walls()')
        # thumb, self.wallbuilder.walls
        shape = self.helper.union([self.wallbuilder.wall_brace(self.ml_place, -0.3, 1, self.connector.web_post_tr(), self.ml_place, 0, 1, self.connector.web_post_tl())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.bl_place, 0, 1, self.connector.web_post_tr(), self.bl_place, 0, 1, self.connector.web_post_tl())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.bl_place, -1, 0, self.connector.web_post_tl(), self.bl_place, -1, 0, self.connector.web_post_bl())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.bl_place, -1, 0, self.connector.web_post_tl(), self.bl_place, 0, 1, self.connector.web_post_tl())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.ml_place, 0, 1, self.connector.web_post_tl(), self.bl_place, 0, 1, self.connector.web_post_tr())])

        corner = self.helper.box(1, 1, self.tbcj_thickness)

        points = [
            (self.bl_place, -1, 0, self.connector.web_post_bl()),
            (self.track_place, 0, -1, self.tbcj_web_post(4)),
            (self.track_place, 0, -1, self.tbcj_web_post(3)),
            (self.track_place, 0, -1, self.tbcj_web_post(2)),
            (self.track_place, 1, -1, self.tbcj_web_post(1)),
            (self.track_place, 1, 0, self.tbcj_web_post(0)),
            ((lambda sh: self.capbuilder.cluster_key_place(sh, 3, self.settings["lastrow"])), 0, -1, self.connector.web_post_bl()),
        ]
        for i, _ in enumerate(points[:-1]):
            (pa, dxa, dya, sa) = points[i]
            (pb, dxb, dyb, sb) = points[i + 1]

            shape = self.helper.union([shape, self.wallbuilder.wall_brace(pa, dxa, dya, sa, pb, dxb, dyb, sb)])

        return shape

    def connection(self, side='right'):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = self.helper.union([self.helper.bottom_hull(
            [
                self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True,
                                              side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True,
                                              side=side),
                               self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                               self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
                               self.tl_place(self.connector.web_post_tl()),
                           ]
                       )
                       ])  # )

        shape = self.helper.union([shape, self.helper.hull_from_shapes(
            [
                self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.tl_place(self.connector.web_post_tl()),
            ]
        )])

        shape = self.helper.union([shape, self.helper.hull_from_shapes(
            [
                self.capbuilder.left_cluster_key_place(self.connector.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                self.tl_place(self.connector.web_post_tl()),
            ]
        )])

        shape = self.helper.union([shape, self.helper.hull_from_shapes(
            [
                self.ml_place(self.connector.web_post_tr()),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate1(-0.3, 1))),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
                self.tl_place(self.connector.web_post_tl()),
            ]
        )])

        return shape

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array([-72, -40, -16]))
        position[2] = 0

        return position
