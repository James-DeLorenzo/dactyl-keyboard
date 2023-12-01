import json
import os
import numpy as np
import logging
from utils import connectors
from utils.caps import CapBuilder


logger = logging.getLogger()

class DefaultCluster(object):
    num_keys = 6
    is_tb = False
    thumb_offsets = [
        6,
        -3,
        8
    ]
    thumb_screw = [-24, -65, 0]
    thumb_plate_tr_rotation = 0
    thumb_plate_tl_rotation = 0
    thumb_plate_mr_rotation = 0
    thumb_plate_ml_rotation = 0
    thumb_plate_br_rotation = 0
    thumb_plate_bl_rotation = 0

    name = "DEFAULT"


    def get_config(self):
        with open(os.path.join("src", "clusters", "json", f"{self.name}.json"), mode='r') as fid:
            data = json.load(fid)
        for item in data:
            if not hasattr(self, str(item)):
                continue
            logger.warning(f"{self.name}: NO MEMBER VARIABLE FOR " + str(item))
            setattr(self, str(item), data[item])
        return data

    def __init__(self, settings: dict, helper, wallbuilder, connector: connectors.WebConnector):
        self.get_config()
        logger.info(f"{self.name} built")
        self.settings = settings
        self.helper = helper
        self.connector = connector
        self.wallbuilder = wallbuilder
        self.capbuilder = CapBuilder(self.settings, self.helper)

    def thumborigin(self):
        # debugprint('thumborigin()')
        origin = self.capbuilder.key_position([self.settings["mount_width"] / 2, -(self.settings["mount_height"] / 2), 0], 1, self.settings["cornerrow"])
        _thumb_offsets = self.thumb_offsets.copy()
        _thumb_offsets = [a + b for a,b in zip(_thumb_offsets, self.settings["thumb_offsets"])]
        if self.settings["shift_column"] != 0:
            _thumb_offsets[0] = self.thumb_offsets[0] + (self.settings["shift_column"] * (self.settings["mount_width"] + 6))
            # if shift_column < 0:  # raise cluster up when moving inward
            #     _thumb_offsets[1] = self.thumb_offsets[1] - (shift_column * 3)
            #     _thumb_offsets[2] = self.thumb_offsets[2] - (shift_column * 8)
            #     if shift_column <= -2:
            #         # y = shift_column * 15
            #         _thumb_offsets[1] = self.thumb_offsets[1] - (shift_column * 15)
        origin = [a + b for a,b in zip(origin, _thumb_offsets)]

        return origin

    def thumb_rotate(self):
        x = y = z = 0
        if self.settings["shift_column"] != 0:
            y = self.settings["shift_column"] * 8
            if self.settings["shift_column"] < 0:
                z = self.settings["shift_column"] * -10
        return [x, y, z]

    def thumb_place(self, shape):
        shape = self.helper.translate(shape, self.thumborigin())
        return self.helper.rotate(shape, self.thumb_rotate())

    def tl_place(self, shape):
        logger.debug('tl_place()')
        shape = self.helper.rotate(shape, [7.5, -18, 10])
        shape = self.helper.translate(shape, [-32.5, -14.5, -2.5])
        shape = self.thumb_place(shape)
        return shape

    def tr_place(self, shape):
        logger.debug('tr_place()')
        shape = self.helper.rotate(shape, [10, -15, 10])
        shape = self.helper.translate(shape, [-12, -16, 3])
        shape = self.thumb_place(shape)
        return shape

    def mr_place(self, shape):
        logger.debug('mr_place()')
        shape = self.helper.rotate(shape, [-6, -34, 48])
        shape = self.helper.translate(shape, [-29, -40, -13])
        shape = self.thumb_place(shape)
        return shape

    def ml_place(self, shape):
        logger.debug('ml_place()')
        shape = self.helper.rotate(shape, [6, -34, 40])
        shape = self.helper.translate(shape, [-51, -25, -12])
        shape = self.thumb_place(shape)
        return shape

    def br_place(self, shape):
        logger.debug('br_place()')
        shape = self.helper.rotate(shape, [-16, -33, 54])
        shape = self.helper.translate(shape, [-37.8, -55.3, -25.3])
        shape = self.thumb_place(shape)
        return shape

    def bl_place(self, shape):
        logger.debug('bl_place()')
        shape = self.helper.rotate(shape, [-4, -35, 52])
        shape = self.helper.translate(shape, [-56.3, -43.3, -23.5])
        shape = self.thumb_place(shape)
        return shape

    def thumb_1x_layout(self, shape, cap=False):
        logger.debug('thumb_1x_layout()')
        if cap:
            shape_list = [
                self.mr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
                self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
                self.br_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
                self.bl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            ]

            if self.settings["default_1U_cluster"]:
                shape_list.append(self.tr_place(self.helper.rotate(self.helper.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
                shape_list.append(self.tr_place(self.helper.rotate(self.helper.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
                shape_list.append(self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation])))
            shapes = self.helper.add(shape_list)

        else:
            shape_list = [
                self.mr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
                self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
                self.br_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
                self.bl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            ]
            if self.settings["default_1U_cluster"]:
                shape_list.append(self.tr_place(self.helper.rotate(self.helper.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
            shapes = self.helper.union(shape_list)
        return shapes

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        logger.debug('thumb_15x_layout()')
        if plate:
            if cap:
                shape = self.helper.rotate(shape, (0, 0, 90))
                cap_list = [self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation]))]
                cap_list.append(self.tr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])))
                return self.helper.add(cap_list)
            else:
                shape_list = [self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation]))]
                if not self.settings["default_1U_cluster"]:
                    shape_list.append(self.tr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])))
                return self.helper.union(shape_list)
        else:
            if cap:
                shape = self.helper.rotate(shape, (0, 0, 90))
                shape_list = [
                    self.tl_place(shape),
                ]
                shape_list.append(self.tr_place(shape))

                return self.helper.add(shape_list)
            else:
                shape_list = [
                    self.tl_place(shape),
                ]
                if not self.settings["default_1U_cluster"]:
                    shape_list.append(self.tr_place(shape))

                return self.helper.union(shape_list)

    def thumbcaps(self, side='right'):
        t1 = self.thumb_1x_layout(self.helper.sa_cap(1), cap=True)
        if not self.settings["default_1U_cluster"]:
            t1.add(self.thumb_15x_layout(self.helper.sa_cap(1.5), cap=True))
        return t1

    def thumb(self, side="right"):
        logger.debug('thumb()')
        shape = self.thumb_1x_layout(self.helper.rotate(self.helper.single_plate(side=side), (0, 0, -90)))
        shape = self.helper.union([shape, self.thumb_15x_layout(self.helper.rotate(self.helper.single_plate(side=side), (0, 0, -90)))])
        shape = self.helper.union([shape, self.thumb_15x_layout(self.helper.double_plate(), plate=False)])

        return shape

    def thumb_post_tr(self):
        logger.debug('thumb_post_tr()')
        return self.helper.translate(self.connector.web_post(),
                         [(self.settings["mount_width"] / 2) - self.settings["post_adj"], ((self.settings["mount_height"] / 2) + self.settings["double_plate_height"]) - self.settings["post_adj"], 0]
                         )

    def thumb_post_tl(self):
        logger.debug('thumb_post_tl()')
        return self.helper.translate(self.connector.web_post(),
                         [-(self.settings["mount_width"] / 2) + self.settings["post_adj"], ((self.settings["mount_height"] / 2) + self.settings["double_plate_height"]) - self.settings["post_adj"], 0]
                         )

    def thumb_post_bl(self):
        logger.debug('thumb_post_bl()')
        return self.helper.translate(self.connector.web_post(),
                         [-(self.settings["mount_width"] / 2) + self.settings["post_adj"], -((self.settings["mount_height"] / 2) + self.settings["double_plate_height"]) + self.settings["post_adj"], 0]
                         )

    def thumb_post_br(self):
        logger.debug('thumb_post_br()')
        return self.helper.translate(self.connector.web_post(),
                         [(self.settings["mount_width"] / 2) - self.settings["post_adj"], -((self.settings["mount_height"] / 2) + self.settings["double_plate_height"]) + self.settings["post_adj"], 0]
                         )

    def thumb_connectors(self, side="right"):
        logger.debug('default thumb_self.connectors()')
        hulls = []

        # Top two
        if self.settings["default_1U_cluster"]:
            hulls.append(
                self.helper.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tr()),
                        self.tl_place(self.thumb_post_br()),
                        self.tr_place(self.connector.web_post_tl()),
                        self.tr_place(self.connector.web_post_bl()),
                    ]
                )
            )
        else:
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
                    self.br_place(self.connector.web_post_tr()),
                    self.br_place(self.connector.web_post_br()),
                    self.mr_place(self.connector.web_post_tl()),
                    self.mr_place(self.connector.web_post_bl()),
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
                    self.br_place(self.connector.web_post_tl()),
                    self.bl_place(self.connector.web_post_bl()),
                    self.br_place(self.connector.web_post_tr()),
                    self.bl_place(self.connector.web_post_br()),
                    self.mr_place(self.connector.web_post_tl()),
                    self.ml_place(self.connector.web_post_bl()),
                    self.mr_place(self.connector.web_post_tr()),
                    self.ml_place(self.connector.web_post_br()),
                ]
            )
        )

        if self.settings["default_1U_cluster"]:
            hulls.append(
                self.helper.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.ml_place(self.connector.web_post_tr()),
                        self.tl_place(self.thumb_post_bl()),
                        self.ml_place(self.connector.web_post_br()),
                        self.tl_place(self.thumb_post_br()),
                        self.mr_place(self.connector.web_post_tr()),
                        self.tr_place(self.connector.web_post_bl()),
                        self.mr_place(self.connector.web_post_br()),
                        self.tr_place(self.connector.web_post_br()),
                    ]
                )
            )
        else:
            # top two to the main keyboard, starting on the left
            hulls.append(
                self.helper.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.ml_place(self.connector.web_post_tr()),
                        self.tl_place(self.thumb_post_bl()),
                        self.ml_place(self.connector.web_post_br()),
                        self.tl_place(self.thumb_post_br()),
                        self.mr_place(self.connector.web_post_tr()),
                        self.tr_place(self.thumb_post_bl()),
                        self.mr_place(self.connector.web_post_br()),
                        self.tr_place(self.thumb_post_br()),
                    ]
                )
            )

        if self.settings["default_1U_cluster"]:
            hulls.append(
                self.helper.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                        self.tl_place(self.thumb_post_tr()),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),
                        self.tr_place(self.connector.web_post_tl()),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),
                        self.tr_place(self.connector.web_post_tr()),
                        self.helper.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                        self.tr_place(self.connector.web_post_tr()),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                        self.tr_place(self.connector.web_post_br()),
                        self.helper.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tr(), 2, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tl(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["cornerrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_br(), 3, self.settings["cornerrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 4, self.settings["cornerrow"]),
                    ]
                )
            )
        else:
            hulls.append(
                self.helper.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                        self.tl_place(self.thumb_post_tr()),
                        self.helper.cluster_key_place(self.connector.web_post_br(), 0, self.settings["cornerrow"]),
                        self.tr_place(self.thumb_post_tl()),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),
                        self.tr_place(self.thumb_post_tr()),
                        self.helper.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                        self.tr_place(self.thumb_post_tr()),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                        self.tr_place(self.thumb_post_br()),
                        self.helper.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tr(), 2, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tl(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["cornerrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_br(), 3, self.settings["cornerrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 4, self.settings["cornerrow"]),
                    ]
                )
            )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.helper.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                    self.helper.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                    self.helper.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["cornerrow"]),
                    self.helper.cluster_key_place(self.connector.web_post_tr(), 2, self.settings["lastrow"]),
                    self.helper.cluster_key_place(self.connector.web_post_br(), 2, self.settings["cornerrow"]),
                    self.helper.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["cornerrow"]),
                ]
            )
        )

        if not self.settings["full_last_rows"]:
            hulls.append(
                self.helper.triangle_hulls(
                    [
                        self.helper.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_br(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_tr(), 3, self.settings["lastrow"]),
                        self.helper.cluster_key_place(self.connector.web_post_bl(), 4, self.settings["cornerrow"]),
                    ]
                )
            )

        return self.helper.union(hulls)

    def walls(self, side="right"):
        logger.debug('thumb_walls()')
        # thumb, walls
        if self.settings["default_1U_cluster"]:
            shape = self.helper.union([self.helper.wall_brace(self.mr_place, 0, -1, self.connector.web_post_br(), self.tr_place, 0, -1, self.connector.web_post_br())])
        else:
            shape = self.helper.union([self.helper.wall_brace(self.mr_place, 0, -1, self.connector.web_post_br(), self.tr_place, 0, -1, self.thumb_post_br())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.mr_place, 0, -1, self.connector.web_post_br(), self.mr_place, 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.br_place, 0, -1, self.connector.web_post_br(), self.br_place, 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.ml_place, -0.3, 1, self.connector.web_post_tr(), self.ml_place, 0, 1, self.connector.web_post_tl())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.bl_place, 0, 1, self.connector.web_post_tr(), self.bl_place, 0, 1, self.connector.web_post_tl())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.br_place, -1, 0, self.connector.web_post_tl(), self.br_place, -1, 0, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.bl_place, -1, 0, self.connector.web_post_tl(), self.bl_place, -1, 0, self.connector.web_post_bl())])
        # thumb, corners
        shape = self.helper.union([shape, self.helper.wall_brace(self.br_place, -1, 0, self.connector.web_post_bl(), self.br_place, 0, -1, self.connector.web_post_bl())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.bl_place, -1, 0, self.connector.web_post_tl(), self.bl_place, 0, 1, self.connector.web_post_tl())])
        # thumb, tweeners
        shape = self.helper.union([shape, self.helper.wall_brace(self.mr_place, 0, -1, self.connector.web_post_bl(), self.br_place, 0, -1, self.connector.web_post_br())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.ml_place, 0, 1, self.connector.web_post_tl(), self.bl_place, 0, 1, self.connector.web_post_tr())])
        shape = self.helper.union([shape, self.helper.wall_brace(self.bl_place, -1, 0, self.connector.web_post_bl(), self.br_place, -1, 0, self.connector.web_post_tl())])
        if self.settings["default_1U_cluster"]:
            shape = self.helper.union([shape,
                           self.helper.wall_brace(self.tr_place, 0, -1, self.connector.web_post_br(), (lambda sh: self.helper.cluster_key_place(sh, 3, self.settings["lastrow"])), 0,
                                      -1, self.connector.web_post_bl())])
        else:
            shape = self.helper.union([shape, self.helper.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(),
                                             (lambda sh: self.helper.cluster_key_place(sh, 3, self.settings["lastrow"])), 0, -1, self.connector.web_post_bl())])

        return shape

    def connection(self, side='right'):
        logger.debug('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal self.connectors don't work well)
        shape = self.helper.union([self.helper.bottom_hull(
            [
                self.helper.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.helper.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.helper.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.helper.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.helper.wall_locate2(-0.3, 1))),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.helper.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.helper.union([shape,
                       self.helper.hull_from_shapes(
                           [
                               self.helper.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.helper.wall_locate2(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.helper.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.helper.wall_locate3(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.helper.wall_locate2(-0.3, 1))),
                               self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.helper.wall_locate3(-0.3, 1))),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )
                       ])  # )

        shape = self.helper.union([shape, self.helper.hull_from_shapes(
            [
                self.helper.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.helper.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.helper.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.helper.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.helper.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.helper.wall_locate3(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.helper.union([shape, self.helper.hull_from_shapes(
            [
                self.helper.left_cluster_key_place(self.connector.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.helper.left_cluster_key_place(self.helper.translate(self.connector.web_post(), self.helper.wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.helper.key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.helper.union([shape, self.helper.hull_from_shapes(
            [
                self.ml_place(self.connector.web_post_tr()),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.helper.wall_locate1(-0.3, 1))),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.helper.wall_locate2(-0.3, 1))),
                self.ml_place(self.helper.translate(self.connector.web_post_tr(), self.helper.wall_locate3(-0.3, 1))),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.helper.union([shape, self.helper.hull_from_shapes(
            [
                self.tl_place(self.thumb_post_tl()),
                self.helper.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                self.helper.key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                # self.helper.left_cluster_key_place(self.connector.web_post_bl(), self.settings["cornerrow"], 0, low_corner=False, side=side),
                self.helper.translate(self.helper.key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]), self.helper.wall_locate1(-1, 0)),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        # shape = union([shape, key_place(sphere(5), 0, self.settings["cornerrow"])])

        return shape

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array(self.thumb_screw))
        position[2] = 0

        return position

    def get_extras(self, shape, pos):
        return shape

    def has_btus(self):
        return False
