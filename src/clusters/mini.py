from clusters.default_cluster import DefaultCluster
import numpy as np
import json
import os
import logging
from utils import plate

logger = logging.getLogger()


class MiniCluster(DefaultCluster):
    name = "MINI"
    num_keys = 5

    def get_config(self):
        with open(os.path.join("src", "clusters", "json", "MINI.json"), mode='r') as fid:
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

    def thumborigin(self):
        # logger.debug('thumborigin()')
        origin = super().thumborigin()
        origin[2] = origin[2] - 4
        return origin

    def tl_place(self, shape):
        shape = self.helper.rotate(shape, [10, -23, 25])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-35, -16, -2])
        return shape

    def tr_place(self, shape):
        shape = self.helper.rotate(shape, [14, -15, 10])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-15, -10, 5])
        return shape

    def mr_place(self, shape):
        shape = self.helper.rotate(shape, [10, -23, 25])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-23, -34, -6])
        return shape

    def br_place(self, shape):
        shape = self.helper.rotate(shape, [6, -34, 35])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-39, -43, -16])
        return shape

    def bl_place(self, shape):
        shape = self.helper.rotate(shape, [6, -32, 35])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-51, -25, -11.5])
        return shape

    def fl_place(self, shape):
        shape = self.helper.rotate(shape, [0, -32, 40])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-25, -45, -15.5])
        return shape

    def thumb_1x_layout(self, shape, cap=False):
        logger.debug('thumb_1x_layout()')
        return self.helper.self.helper.union([
            self.mr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
            self.br_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
            self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation])),
            self.bl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
        ])


    def thumb_15x_layout(self, shape, cap=False, plate=True):
        logger.debug('thumb_15x_layout()')
        return self.helper.self.helper.union([self.tr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation]))])

    def thumbcaps(self, side='right'):
        t1 = self.thumb_1x_layout(self.capbuilder.sa_cap(1))
        t15 = self.thumb_15x_layout(self.helper.rotate(self.capbuilder.sa_cap(1), [0, 0, np.rad2deg(np.pi / 2)]))
        return t1.add(t15)

    def thumb(self, side="right"):
        logger.info('thumb()')
        shape = self.thumb_1x_layout(plate.single_plate(self.settings, self.helper, side=side))
        shape = self.helper.self.helper.union([shape, self.thumb_15x_layout(plate.single_plate(self.settings, self.helper, side=side))])

        return shape

    def thumb_post_tr(self):
        logger.debug('thumb_post_tr()')
        return self.helper.translate(self.connector.web_post(),
                         [(self.settings["mount_width"] / 2) - self.settings["post_adj"], (self.settings["mount_height"] / 2) - self.settings["post_adj"], 0]
                    )

    def thumb_post_tl(self):
        logger.debug('thumb_post_tl()')
        return self.helper.translate(self.connector.web_post(),
                         [-(self.settings["mount_width"] / 2) + self.settings["post_adj"], (self.settings["mount_height"] / 2) - self.settings["post_adj"], 0]
                    )

    def thumb_post_bl(self):
        logger.debug('thumb_post_bl()')
        return self.helper.translate(self.connector.web_post(),
                         [-(self.settings["mount_width"] / 2) + self.settings["post_adj"], -(self.settings["mount_height"] / 2) + self.settings["post_adj"], 0]
                    )

    def thumb_post_br(self):
        logger.debug('thumb_post_br()')
        return self.helper.translate(self.connector.web_post(),
                         [(self.settings["mount_width"] / 2) - self.settings["post_adj"], -(self.settings["mount_height"] / 2) + self.settings["post_adj"], 0]
                    )

    def thumb_connectors(self, side="right"):
        print('thumb_connectors()')
        hulls = []

        # Top two
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_br()),
                    self.tr_place(self.thumb_post_tl()),
                    self.tr_place(self.thumb_post_bl()),
                ]
            )
        )

        # bottom two on the right
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.br_place(self.connector.web_post_tr()),
                    self.br_place(self.connector.web_post_br()),
                    self.mr_place(self.connector.web_post_tl()),
                    self.mr_place(self.connector.web_post_bl()),
                ]
            )
        )

        # bottom two on the left
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.mr_place(self.connector.web_post_tr()),
                    self.mr_place(self.connector.web_post_br()),
                    self.tr_place(self.thumb_post_br()),
                ]
            )
        )

        # between top and bottom row
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.br_place(self.connector.web_post_tl()),
                    self.bl_place(self.connector.web_post_bl()),
                    self.br_place(self.connector.web_post_tr()),
                    self.bl_place(self.connector.web_post_br()),
                    self.mr_place(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_bl()),
                    self.mr_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_br()),
                    self.tr_place(self.connector.web_post_bl()),
                    self.mr_place(self.connector.web_post_tr()),
                    self.tr_place(self.connector.web_post_br()),
                ]
            )
        )
        # top two to the main keyboard, starting on the left
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl()),
                    self.bl_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_bl()),
                    self.bl_place(self.connector.web_post_br()),
                    self.mr_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_bl()),
                    self.tl_place(self.connector.web_post_br()),
                    self.mr_place(self.connector.web_post_tr()),
                ]
            )
        )
        # top two to the main keyboard, starting on the left
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.tl_place(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 0, self.settings["cornerrow"]),
                    self.tr_place(self.thumb_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),
                    self.tr_place(self.thumb_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tr_place(self.thumb_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tr_place(self.thumb_post_br()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 3, self.settings["cornerrow"]),
                ]
            )
        )
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 4, self.settings["cornerrow"]),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
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

        return self.helper.union(hulls)

    def walls(self, side="right"):
        print('walls()')
        # thumb, self.wallbuilder.walls
        shape = self.helper.union([self.wallbuilder.wall_brace(self.mr_place, 0, -1, self.connector.web_post_br(), self.tr_place, 0, -1, self.thumb_post_br())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.mr_place, 0, -1, self.connector.web_post_br(), self.mr_place, 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.br_place, 0, -1, self.connector.web_post_br(), self.br_place, 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.bl_place, 0, 1, self.connector.web_post_tr(), self.bl_place, 0, 1, self.connector.web_post_tl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.br_place, -1, 0, self.connector.web_post_tl(), self.br_place, -1, 0, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.bl_place, -1, 0, self.connector.web_post_tl(), self.bl_place, -1, 0, self.connector.web_post_bl())])
        # thumb, corners
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.br_place, -1, 0, self.connector.web_post_bl(), self.br_place, 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.bl_place, -1, 0, self.connector.web_post_tl(), self.bl_place, 0, 1, self.connector.web_post_tl())])
        # thumb, tweeners
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.mr_place, 0, -1, self.connector.web_post_bl(), self.br_place, 0, -1, self.connector.web_post_br())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.bl_place, -1, 0, self.connector.web_post_bl(), self.br_place, -1, 0, self.connector.web_post_tl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(), (lambda sh: self.capbuilder.cluster_key_place(sh, 3, self.settings["lastrow"])), 0, -1, self.connector.web_post_bl())])

        return shape


    def connection(self, side='right'):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = self.helper.union([self.helper.bottom_hull(
            [
                self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.bl_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                self.bl_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.bl_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                               self.bl_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
                               self.tl_place(self.connector.web_post_tl()),
                           ]
                       )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_cluster_key_place(self.connector.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.tl_place(self.connector.web_post_tl()),
                           ]
                       )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_cluster_key_place(self.connector.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                               self.tl_place(self.connector.web_post_tl()),
                           ]
                       )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.bl_place(self.connector.web_post_tr()),
                               self.bl_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate1(-0.3, 1))),
                               self.bl_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                               self.bl_place(self.helper.translate(self.connector.web_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
                               self.tl_place(self.connector.web_post_tl()),
                           ]
                       )])

        return shape

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array([-29, -51, -16]))
        position[2] = 0

        return position
