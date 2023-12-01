from clusters.default_cluster import DefaultCluster
import numpy as np
import json
import os
import logging
from utils import plate

logger = logging.getLogger()

class CarbonfetCluster(DefaultCluster):
    name = "CARBONFET"

    def get_config(self):
        with open(os.path.join("src", "clusters", "json", f"{self.name}.json"), mode='r') as fid:
            data = json.load(fid)

        superdata = super().get_config()

        # overwrite any super variables with this class' needs
        for item in data:
            superdata[item] = data[item]

        for item in superdata:
            if not hasattr(self, str(item)):
                logger.warn(f"{self.name}: NO MEMBER VARIABLE FOR {str(item)}")
                continue
            setattr(self, str(item), superdata[item])

        return superdata

    def __init__(self, *args, **kwargs):
        logger.debug(args)
        logger.debug(kwargs)
        super().__init__(*args, **kwargs)
        self.super = super()

    def tl_place(self, shape):
        shape = self.helper.rotate(shape, [10, -24, 10])
        # shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-13, -9.8, 4])
        shape = self.thumb_place(shape)
        return shape

    def tl_wall(self, shape):
        return self.helper.translate(self.tl_place(shape), (1.7, 1, 0))

    def tr_place(self, shape):
        shape = self.helper.rotate(shape, [6, -25, 10])
        # shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-7.5, -29.5, 0])
        shape = self.thumb_place(shape)
        return shape


    def ml_place(self, shape):
        shape = self.helper.rotate(shape, [8, -31, 14])
        # shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-30.5, -17, -6])
        shape = self.thumb_place(shape)
        return shape

    def mr_place(self, shape):
        shape = self.helper.rotate(shape, [4, -31, 14])
        # shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-22.2, -41, -10.3])
        shape = self.thumb_place(shape)
        return shape

    def br_place(self, shape):
        shape = self.helper.rotate(shape, [2, -37, 18])
        # shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-37, -46.4, -22])
        shape = self.thumb_place(shape)
        return shape

    def bl_place(self, shape):
        shape = self.helper.rotate(shape, [6, -37, 18])
        # shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-47, -23, -19])
        shape = self.thumb_place(shape)
        return shape

    def thumb_1x_layout(self, shape, cap=False):
        logger.debug('thumb_1x_layout()')
        return self.helper.union([
            self.tr_place(self.helper.rotate(shape, [0, 0, self.settings["thumb_plate_tr_rotation"]])),
            self.mr_place(self.helper.rotate(shape, [0, 0, self.settings["thumb_plate_mr_rotation"]])),
            self.br_place(self.helper.rotate(shape, [0, 0, self.settings["thumb_plate_br_rotation"]])),
            self.tl_place(self.helper.rotate(shape, [0, 0, self.settings["thumb_plate_tl_rotation"]])),
        ])

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        logger.debug('thumb_15x_layout()')
        if plate:
            return self.helper.union([
                self.bl_place(self.helper.rotate(shape, [0, 0, self.settings["thumb_plate_bl_rotation"]])),
                self.ml_place(self.helper.rotate(shape, [0, 0, self.settings["thumb_plate_ml_rotation"]]))
            ])
        else:
            return self.helper.union([
                self.bl_place(shape),
                self.ml_place(shape)
            ])

    def thumbcaps(self, side='right'):
        t1 = self.thumb_1x_layout(self.capbuilder.sa_cap(1))
        t15 = self.thumb_15x_layout(self.helper.rotate(self.capbuilder.sa_cap(1.5), [0, 0, np.rad2deg(np.pi / 2)]))
        return t1.add(t15)

    def thumb(self, side="right"):
        logger.debug('thumb()')
        shape = self.thumb_1x_layout(plate.single_plate(self.settings, self.helper, side=side))
        shape = self.helper.union([shape, self.thumb_15x_layout(plate.double_plate_half(self.settings, self.helper), plate=False)])
        shape = self.helper.union([shape, self.thumb_15x_layout(plate.single_plate(self.settings, self.helper, side=side))])

        return shape

    def thumb_connectors(self, side="right"):
        logger.debug('thumb_connectors()')
        hulls = []

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_wall(self.connector.web_post_tl()),
                    self.tl_wall(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_tl()),
                    self.tl_wall(self.connector.web_post_tl()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_wall(self.connector.web_post_tr()),
                    self.tl_wall(self.connector.web_post_br()),
                    self.tl_place(self.connector.web_post_br()),
                    self.tl_place(self.connector.web_post_tr()),
                    self.tl_wall(self.connector.web_post_tr()),
                ]
            )
        )

        # Top two
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_bl()),
                    self.ml_place(self.thumb_post_tr()),
                    self.ml_place(self.connector.web_post_br()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.ml_place(self.thumb_post_tl()),
                    self.ml_place(self.connector.web_post_bl()),
                    self.bl_place(self.thumb_post_tr()),
                    self.bl_place(self.connector.web_post_br()),
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
                    self.tr_place(self.connector.web_post_tl()),
                    self.tr_place(self.connector.web_post_bl()),
                ]
            )
        )
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tr_place(self.connector.web_post_br()),
                    self.tr_place(self.connector.web_post_bl()),
                    self.mr_place(self.connector.web_post_br()),
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
                    self.ml_place(self.connector.web_post_bl()),
                    self.mr_place(self.connector.web_post_tr()),
                    self.ml_place(self.connector.web_post_br()),
                    self.tr_place(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_bl()),
                    self.tr_place(self.connector.web_post_tr()),
                    self.tl_wall(self.connector.web_post_br()),
                ]
            )
        )
        # top two to the main keyboard, starting on the left
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.ml_place(self.thumb_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),

                    self.ml_place(self.thumb_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 0, self.settings["cornerrow"]),
                    self.tl_place(self.connector.web_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),
                    self.tl_wall(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tl_wall(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tl_wall(self.connector.web_post_br()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                    self.tl_wall(self.connector.web_post_br()),
                    self.tr_place(self.connector.web_post_tr()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 3, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["cornerrow"]),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                ]
            )
        )
        #
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tr_place(self.connector.web_post_br()),
                    self.tr_place(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                ]
            )
        )
        #
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["cornerrow"]),
                ]
            )
        )
        #
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 4, self.capbuilder.bottom_key(self.capbuilder.col(4))),
                ]
            )
        )
        #
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 3, self.settings["cornerrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 4, self.capbuilder.bottom_key(self.capbuilder.col(4))),
                ]
            )
        )

        return self.helper.union(hulls)

    def walls(self, side="right"):
        logger.debug('thumb_walls()')
        # thumb, walls
        shape = self.helper.union([self.wallbuilder.wall_brace(self.mr_place, 0, -1, self.connector.web_post_br(), self.tr_place, 0, -1, self.connector.web_post_br())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.mr_place, 0, -1, self.connector.web_post_br(), self.mr_place, 0, -1.15, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.br_place, 0, -1, self.connector.web_post_br(), self.br_place, 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.bl_place, -.3, 1, self.thumb_post_tr(), self.bl_place, 0, 1, self.thumb_post_tl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.br_place, -1, 0, self.connector.web_post_tl(), self.br_place, -1, 0, self.connector.web_post_bl())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.bl_place, -1, 0, self.thumb_post_tl(), self.bl_place, -1, 0, self.connector.web_post_bl())])
        # thumb, corners
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.br_place, -1, 0, self.connector.web_post_bl(), self.br_place, 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.bl_place, -1, 0, self.thumb_post_tl(), self.bl_place, 0, 1, self.thumb_post_tl())])
        # thumb, tweeners
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.mr_place, 0, -1.15, self.connector.web_post_bl(), self.br_place, 0, -1, self.connector.web_post_br())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.bl_place, -1, 0, self.connector.web_post_bl(), self.br_place, -1, 0, self.connector.web_post_tl())])
        shape = self.helper.union([shape,
                       self.wallbuilder.wall_brace(self.tr_place, 0, -1, self.connector.web_post_br(), (lambda sh: self.capbuilder.cluster_key_place(sh, 3, self.settings["lastrow"])), 0, -1,
                                  self.connector.web_post_bl())])
        return shape

    def connection(self, side='right'):
        logger.debug('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = self.helper.bottom_hull(
            [
                self.capbuilder.left_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.capbuilder.left_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0.2)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
            ]
        )

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.capbuilder.left_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                               self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
                               self.ml_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_key_place(self.connector.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.capbuilder.left_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.capbuilder.left_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.ml_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_key_place(self.connector.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.capbuilder.key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                               self.ml_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.bl_place(self.thumb_post_tr()),
                               self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate1(-0.3, 1))),
                               self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                               self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
                               self.ml_place(self.thumb_post_tl()),
                           ]
                       )])

        return shape

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array([-48, -37, 0]))
        position[2] = 0

        return position
