from clusters.minidox import MinidoxCluster
import os
import json
import numpy as np
import logging
from utils import plate

logger = logging.getLogger()

class Minithicc(MinidoxCluster):
    name = "MINITHICC"
    num_keys = 4

    def __init__(self, *args, **kwargs):
        logger.debug(args)
        logger.debug(kwargs)
        super().__init__(*args, **kwargs)
        self.super = super()

    def get_config(self):
        with open(os.path.join("src", "clusters", "json", "MINITHICC.json"), mode='r') as fid:
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

    # def tl_place(self, shape):
    #     shape = self.helper.rotate(shape, [14, -15, 20])
    #     shape = self.helper.translate(shape, self.thumborigin())
    #     shape = self.helper.translate(shape, [-45, -16, -15])
    #     return shape
    #
    # def tr_place(self, shape):
    #     shape = self.helper.rotate(shape, [17, -15, 10])
    #     shape = self.helper.translate(shape, self.thumborigin())
    #     shape = self.helper.translate(shape, [-25, -10, -9])
    #     return shape
    #
    # def ml_place(self, shape):
    #     shape = self.helper.rotate(shape, [10, -15, 30])
    #     shape = self.helper.translate(shape, self.thumborigin())
    #     shape = self.helper.translate(shape, [-64, -26, -21])
    #     return shape

    def tr_place(self, shape):
        shape = self.helper.rotate(shape, [19, -15, 2])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-14, -11, -3])
        return shape

    def tl_place(self, shape):
        shape = self.helper.rotate(shape, [17, -15, 10])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-35, -13, -9])
        return shape

    def mr_place(self, shape):
        shape = self.helper.rotate(shape, [14, -15, 20])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-55, -19, -15])
        return shape

    def ml_place(self, shape):
        shape = self.helper.rotate(shape, [10, -15, 28])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-73, -28, -21])
        return shape




    #
    # def br_place(self, shape):
    #     shape = self.helper.rotate(shape, [6, -32, 35])
    #     shape = self.helper.translate(shape, self.thumborigin())
    #     shape = self.helper.translate(shape, [-51, -25, -11.5])
    #     return shape
    #
    # def bl_place(self, shape):
    #     shape = self.helper.rotate(shape, [6, -32, 35])
    #     shape = self.helper.translate(shape, self.thumborigin())
    #     shape = self.helper.translate(shape, [-51, -25, -11.5])
    #     return shape
    #
    # def fl_place(self, shape):
    #     shape = self.helper.rotate(shape, [0, -32, 40])
    #     shape = self.helper.translate(shape, self.thumborigin())
    #     shape = self.helper.translate(shape, [-25, -45, -15.5])
    #     return shape

    def thumb_1x_layout(self, shape, cap=False):
        logger.debug('thumb_1x_layout()')
        # return self.helper.union([
        #     self.tr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])),
        #     self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation])),
        #     self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
        # ])

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        logger.debug('thumb_15x_layout()')
        return self.helper.union([
            self.tr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])),
            self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation])),
            self.mr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
            self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
        ])

    def thumb_fx_layout(self, shape):
        return self.helper.union([
            self.tr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])),
            self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation])),
            self.mr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
            self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
            # self.fl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
        ])

    # def thumb_15x_layout(self, shape, cap=False, plate=True):
    #     logger.debug('thumb_15x_layout()')
    #     if plate:
    #         return self.helper.union([
    #             self.bl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
    #             self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation]))
    #         ])
    #     else:
    #         return self.helper.union([
    #             self.bl_place(shape),
    #             self.ml_place(shape)
    #         ])

    def thumbcaps(self, side='right'):
        t1 = self.thumb_15x_layout(self.capbuilder.sa_cap())
        return t1

    def thumb(self, side="right"):
        print('thumb()')
        shape = self.thumb_fx_layout(self.helper.rotate(plate.single_plate(self.settings, self.helper, side=side), [0.0, 0.0, -90]))
        shape = self.helper.union([shape, self.thumb_fx_layout(plate.adjustable_plate(self.settings, self.helper, self.minidox_Usize))])

        return shape

    def thumb_post_tr(self):
        logger.debug('thumb_post_tr()')
        return self.helper.translate(self.connector.web_post(),
                         [(self.settings["mount_width"] / 2) - self.settings["post_adj"], ((self.settings["mount_height"]/2) + plate.adjustable_plate(self.settings, self.helper, self.minidox_Usize)) - self.settings["post_adj"], 0]
                         )

    def thumb_post_tl(self):
        logger.debug('thumb_post_tl()')
        return self.helper.translate(self.connector.web_post(),
                         [-(self.settings["mount_width"] / 2) + self.settings["post_adj"], ((self.settings["mount_height"]/2) + plate.adjustable_plate(self.settings, self.helper, self.minidox_Usize)) - self.settings["post_adj"], 0]
                         )

    def thumb_post_bl(self):
        logger.debug('thumb_post_bl()')
        return self.helper.translate(self.connector.web_post(),
                         [-(self.settings["mount_width"] / 2) + self.settings["post_adj"], -((self.settings["mount_height"]/2) + plate.adjustable_plate(self.settings, self.helper, self.minidox_Usize)) + self.settings["post_adj"], 0]
                         )

    def thumb_post_br(self):
        logger.debug('thumb_post_br()')
        return self.helper.translate(self.connector.web_post(),
                         [(self.settings["mount_width"] / 2) - self.settings["post_adj"], -((self.settings["mount_height"]/2) + plate.adjustable_plate(self.settings, self.helper, self.minidox_Usize)) + self.settings["post_adj"], 0]
                         )

    def thumb_connectors(self, side="right"):
        print('thumb_connectors()')
        hulls = []

        # Top two
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tr()),
                    self.tl_place(self.thumb_post_br()),
                    self.tr_place(self.thumb_post_tl()),
                    self.tr_place(self.thumb_post_bl()),
                ]
            )
        )

        # bottom two on the right
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tl()),
                    self.tl_place(self.thumb_post_bl()),
                    self.mr_place(self.thumb_post_tr()),
                    self.mr_place(self.thumb_post_br()),
                ]
            )
        )

        # bottom two on the right
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.mr_place(self.thumb_post_tl()),
                    self.mr_place(self.thumb_post_bl()),
                    self.ml_place(self.thumb_post_tr()),
                    self.ml_place(self.thumb_post_br()),
                ]
            )
        )


        # top two to the main self.capbuilder.keyboard, starting on the left
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.thumb_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.tl_place(self.thumb_post_tr()),
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
        shape = self.helper.union([self.wallbuilder.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(), self.tr_place, 0, -1, self.thumb_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.tr_place, 0, -1, self.thumb_post_bl(), self.tl_place, 0, -1, self.thumb_post_br())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.tl_place, 0, -1, self.thumb_post_br(), self.tl_place, 0, -1, self.thumb_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.tl_place, 0, -1, self.thumb_post_bl(), self.ml_place, -1, -1, self.thumb_post_br())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.mr_place, 0, -1, self.thumb_post_br(), self.mr_place, 0, -1, self.thumb_post_bl())])
        shape = self.helper.union(
            [shape, self.wallbuilder.wall_brace(self.mr_place, 0, -1, self.thumb_post_bl(), self.tl_place, 0, -1, self.thumb_post_br())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.ml_place, -1, -1, self.thumb_post_br(), self.ml_place, 0, -1, self.thumb_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.ml_place, 0, -1, self.thumb_post_bl(), self.ml_place, -1, 0, self.thumb_post_bl())])
        # thumb, corners
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.ml_place, -1, 0, self.thumb_post_bl(), self.ml_place, -1, 0, self.thumb_post_tl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.ml_place, -1, 0, self.thumb_post_tl(), self.ml_place, 0, 1, self.thumb_post_tl())])
        # thumb, tweeners
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.mr_place, 0, 1, self.thumb_post_tr(), self.ml_place, 0, 1, self.thumb_post_tl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(), (lambda sh: self.capbuilder.cluster_key_place(sh, 3, self.settings["lastrow"])), 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(self.ml_place, 0, 1, self.thumb_post_tr(), self.ml_place, 0, 1, self.thumb_post_tl())])
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
                self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                self.bl_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.mr_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate2(-0.3, 1))),
                               self.mr_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate3(-0.3, 1))),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )])

        # this one
        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_cluster_key_place(self.connector.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.mr_place(self.thumb_post_tr()),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.capbuilder.left_cluster_key_place(self.connector.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                               # self.capbuilder.cluster_key_place(self.helper.translate(self.connector.web_post_bl(), self.wallbuilder.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True),
                               self.mr_place(self.thumb_post_tr()),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )])


        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.ml_place(self.thumb_post_tr()),
                               self.ml_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate1(0, 1))),
                               self.ml_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate2(0, 1))),
                               self.ml_place(self.helper.translate(self.thumb_post_tr(), self.wallbuilder.wall_locate3(0, 1))),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )])
        return shape

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array([-37, -30, -16]))
        position[1] = position[1] - .4 * (self.minidox_Usize - 1.9) * self.settings["sa_length"]
        position[2] = 0

        return position
