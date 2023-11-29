from clusters.default_cluster import DefaultCluster
import numpy as np
import json
import os

class CarbonfetCluster(DefaultCluster):

    @staticmethod
    def name():
        return "CARBONFET"

    def get_config(self):
        with open(os.path.join("src", "clusters", "json", "CARBONFET.json"), mode='r') as fid:
            data = json.load(fid)

        superdata = super().get_config()

        # overwrite any super variables with this class' needs
        for item in data:
            superdata[item] = data[item]

        for item in superdata:
            if not hasattr(self, str(item)):
                print(self.name() + ": NO MEMBER VARIABLE FOR " + str(item))
                continue
            setattr(self, str(item), superdata[item])

        return superdata

    def __init__(self, settings, helpers):
        super().__init__(settings, helpers)
        # self.settings = setting
        self.helpers = helpers

    def tl_place(self, shape):
        shape = self.helpers.rotate(shape, [10, -24, 10])
        # shape = self.helpers.translate(shape, self.thumborigin())
        shape = self.helpers.translate(shape, [-13, -9.8, 4])
        shape = self.thumb_place(shape)
        return shape

    def tl_wall(self, shape):
        return self.helpers.translate(self.tl_place(shape), (1.7, 1, 0))

    def tr_place(self, shape):
        shape = self.helpers.rotate(shape, [6, -25, 10])
        # shape = self.helpers.translate(shape, self.thumborigin())
        shape = self.helpers.translate(shape, [-7.5, -29.5, 0])
        shape = self.thumb_place(shape)
        return shape


    def ml_place(self, shape):
        shape = self.helpers.rotate(shape, [8, -31, 14])
        # shape = self.helpers.translate(shape, self.thumborigin())
        shape = self.helpers.translate(shape, [-30.5, -17, -6])
        shape = self.thumb_place(shape)
        return shape

    def mr_place(self, shape):
        shape = self.helpers.rotate(shape, [4, -31, 14])
        # shape = self.helpers.translate(shape, self.thumborigin())
        shape = self.helpers.translate(shape, [-22.2, -41, -10.3])
        shape = self.thumb_place(shape)
        return shape

    def br_place(self, shape):
        shape = self.helpers.rotate(shape, [2, -37, 18])
        # shape = self.helpers.translate(shape, self.thumborigin())
        shape = self.helpers.translate(shape, [-37, -46.4, -22])
        shape = self.thumb_place(shape)
        return shape

    def bl_place(self, shape):
        shape = self.helpers.rotate(shape, [6, -37, 18])
        # shape = self.helpers.translate(shape, self.thumborigin())
        shape = self.helpers.translate(shape, [-47, -23, -19])
        shape = self.thumb_place(shape)
        return shape

    def thumb_1x_layout(self, shape, cap=False):
        debugprint('thumb_1x_layout()')
        return self.helpers.union([
            self.tr_place(self.helpers.rotate(shape, [0, 0, self.settings["thumb_plate_tr_rotation"]])),
            self.mr_place(self.helpers.rotate(shape, [0, 0, self.settings["thumb_plate_mr_rotation"]])),
            self.br_place(self.helpers.rotate(shape, [0, 0, self.settings["thumb_plate_br_rotation"]])),
            self.tl_place(self.helpers.rotate(shape, [0, 0, self.settings["thumb_plate_tl_rotation"]])),
        ])

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        debugprint('thumb_15x_layout()')
        if plate:
            return self.helpers.union([
                self.bl_place(self.helpers.rotate(shape, [0, 0, self.settings["thumb_plate_bl_rotation"]])),
                self.ml_place(self.helpers.rotate(shape, [0, 0, self.settings["thumb_plate_ml_rotation"]]))
            ])
        else:
            return self.helpers.union([
                self.bl_place(shape),
                self.ml_place(shape)
            ])

    def thumbcaps(self, side='right'):
        t1 = self.thumb_1x_layout(self.helpers.sa_cap(1))
        t15 = self.thumb_15x_layout(self.helpers.rotate(self.helpers.sa_cap(1.5), [0, 0, rad2deg(pi / 2)]))
        return t1.add(t15)

    def thumb(self, side="right"):
        print('thumb()')
        shape = self.thumb_1x_layout(self.helpers.single_plate(side=side))
        shape = self.helpers.union([shape, self.thumb_15x_layout(self.helpers.double_plate_half(), plate=False)])
        shape = self.helpers.union([shape, self.thumb_15x_layout(self.helpers.single_plate(side=side))])

        return shape

    def thumb_connectors(self, side="right"):
        print('thumb_connectors()')
        hulls = []

        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.tl_wall(self.helpers.web_post_tl()),
                    self.tl_wall(self.helpers.web_post_tr()),
                    self.tl_place(self.helpers.web_post_tr()),
                    self.tl_place(self.helpers.web_post_tl()),
                    self.tl_wall(self.helpers.web_post_tl()),
                ]
            )
        )

        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.tl_wall(self.helpers.web_post_tr()),
                    self.tl_wall(self.helpers.web_post_br()),
                    self.tl_place(self.helpers.web_post_br()),
                    self.tl_place(self.helpers.web_post_tr()),
                    self.tl_wall(self.helpers.web_post_tr()),
                ]
            )
        )

        # Top two
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.tl_place(self.helpers.web_post_tl()),
                    self.tl_place(self.helpers.web_post_bl()),
                    self.ml_place(self.thumb_post_tr()),
                    self.ml_place(self.helpers.web_post_br()),
                ]
            )
        )

        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.ml_place(self.thumb_post_tl()),
                    self.ml_place(self.helpers.web_post_bl()),
                    self.bl_place(self.thumb_post_tr()),
                    self.bl_place(self.helpers.web_post_br()),
                ]
            )
        )

        # bottom two on the right
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.br_place(self.helpers.web_post_tr()),
                    self.br_place(self.helpers.web_post_br()),
                    self.mr_place(self.helpers.web_post_tl()),
                    self.mr_place(self.helpers.web_post_bl()),
                ]
            )
        )

        # bottom two on the left
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.mr_place(self.helpers.web_post_tr()),
                    self.mr_place(self.helpers.web_post_br()),
                    self.tr_place(self.helpers.web_post_tl()),
                    self.tr_place(self.helpers.web_post_bl()),
                ]
            )
        )
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.tr_place(self.helpers.web_post_br()),
                    self.tr_place(self.helpers.web_post_bl()),
                    self.mr_place(self.helpers.web_post_br()),
                ]
            )
        )

        # between top and bottom row
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.br_place(self.helpers.web_post_tl()),
                    self.bl_place(self.helpers.web_post_bl()),
                    self.br_place(self.helpers.web_post_tr()),
                    self.bl_place(self.helpers.web_post_br()),
                    self.mr_place(self.helpers.web_post_tl()),
                    self.ml_place(self.helpers.web_post_bl()),
                    self.mr_place(self.helpers.web_post_tr()),
                    self.ml_place(self.helpers.web_post_br()),
                    self.tr_place(self.helpers.web_post_tl()),
                    self.tl_place(self.helpers.web_post_bl()),
                    self.tr_place(self.helpers.web_post_tr()),
                    self.tl_wall(self.helpers.web_post_br()),
                ]
            )
        )
        # top two to the main keyboard, starting on the left
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.helpers.key_place(self.helpers.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.ml_place(self.thumb_post_tl()),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 0, self.settings["cornerrow"]),

                    self.ml_place(self.thumb_post_tr()),
                    self.helpers.cluster_key_place(self.helpers.web_post_br(), 0, self.settings["cornerrow"]),
                    self.tl_place(self.helpers.web_post_tl()),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 1, self.settings["cornerrow"]),
                    self.tl_wall(self.helpers.web_post_tr()),
                    self.helpers.cluster_key_place(self.helpers.web_post_br(), 1, self.settings["cornerrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_tl(), 2, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tl_wall(self.helpers.web_post_tr()),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tl_wall(self.helpers.web_post_br()),
                    self.helpers.cluster_key_place(self.helpers.web_post_br(), 2, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, self.settings["lastrow"]),
                    self.tl_wall(self.helpers.web_post_br()),
                    self.tr_place(self.helpers.web_post_tr()),
                ]
            )
        )

        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.helpers.cluster_key_place(self.helpers.web_post_tr(), 3, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_br(), 3, self.settings["cornerrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_tl(), 3, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, self.settings["cornerrow"]),
                ]
            )
        )

        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.helpers.cluster_key_place(self.helpers.web_post_tr(), 2, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_br(), 2, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_tl(), 3, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, self.settings["lastrow"]),
                ]
            )
        )
        #
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.tr_place(self.helpers.web_post_br()),
                    self.tr_place(self.helpers.web_post_tr()),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, self.settings["lastrow"]),
                ]
            )
        )
        #
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_br(), 1, self.settings["cornerrow"]),
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_tl(), 2, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_bl(), 2, self.settings["cornerrow"]),
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_tr(), 2, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_br(), 2, self.settings["cornerrow"]),
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_tl(), 3, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_bl(), 3, self.settings["cornerrow"]),
                ]
            )
        )
        #
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_tr(), 3, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_br(), 3, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.self.helpers.web_post_bl(), 4, self.helpers.bottom_key(self.helpers.col(4))),
                ]
            )
        )
        #
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.helpers.cluster_key_place(self.helpers.web_post_tr(), 3, self.settings["lastrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_br(), 3, self.settings["cornerrow"]),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 4, self.helpers.bottom_key(self.helpers.col(4))),
                ]
            )
        )

        return self.helpers.union(hulls)

    def walls(self, side="right"):
        print('thumb_walls()')
        # thumb, walls
        shape = self.helpers.union([self.helpers.wall_brace(self.mr_place, 0, -1, self.helpers.web_post_br(), self.tr_place, 0, -1, self.helpers.web_post_br())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.mr_place, 0, -1, self.helpers.web_post_br(), self.mr_place, 0, -1.15, self.helpers.web_post_bl())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.br_place, 0, -1, self.helpers.web_post_br(), self.br_place, 0, -1, self.helpers.web_post_bl())])
        shape = self.helpers.union(
            [shape, self.helpers.wall_brace(self.bl_place, -.3, 1, self.thumb_post_tr(), self.bl_place, 0, 1, self.thumb_post_tl())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.br_place, -1, 0, self.helpers.web_post_tl(), self.br_place, -1, 0, self.helpers.web_post_bl())])
        shape = self.helpers.union(
            [shape, self.helpers.wall_brace(self.bl_place, -1, 0, self.thumb_post_tl(), self.bl_place, -1, 0, self.helpers.web_post_bl())])
        # thumb, corners
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.br_place, -1, 0, self.helpers.web_post_bl(), self.br_place, 0, -1, self.helpers.web_post_bl())])
        shape = self.helpers.union(
            [shape, self.helpers.wall_brace(self.bl_place, -1, 0, self.thumb_post_tl(), self.bl_place, 0, 1, self.thumb_post_tl())])
        # thumb, tweeners
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.mr_place, 0, -1.15, self.helpers.web_post_bl(), self.br_place, 0, -1, self.helpers.web_post_br())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.bl_place, -1, 0, self.helpers.web_post_bl(), self.br_place, -1, 0, self.helpers.web_post_tl())])
        shape = self.helpers.union([shape,
                       self.helpers.wall_brace(self.tr_place, 0, -1, self.helpers.web_post_br(), (lambda sh: self.helpers.cluster_key_place(sh, 3, self.settings["lastrow"])), 0, -1,
                                  self.helpers.web_post_bl())])
        return shape

    def connection(self, side='right'):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = self.helpers.bottom_hull(
            [
                self.helpers.left_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate2(-1, 0)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.helpers.left_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate3(-1, 0.2)), self.settings["cornerrow"], -1, low_corner=True, side=side),
                self.bl_place(self.helpers.translate(self.thumb_post_tr(), self.helpers.wall_locate2(-0.3, 1))),
                self.bl_place(self.helpers.translate(self.thumb_post_tr(), self.helpers.wall_locate3(-0.3, 1))),
            ]
        )

        shape = self.helpers.union([shape,
                       self.helpers.hull_from_shapes(
                           [
                               self.helpers.left_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate2(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.helpers.left_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate3(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.bl_place(self.helpers.translate(self.thumb_post_tr(), self.helpers.wall_locate2(-0.3, 1))),
                               self.bl_place(self.helpers.translate(self.thumb_post_tr(), self.helpers.wall_locate3(-0.3, 1))),
                               self.ml_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.helpers.union([shape,
                       self.helpers.hull_from_shapes(
                           [
                               self.helpers.left_key_place(self.helpers.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.helpers.left_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate1(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.helpers.left_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate2(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.helpers.left_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate3(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.ml_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.helpers.union([shape,
                       self.helpers.hull_from_shapes(
                           [
                               self.helpers.left_key_place(self.helpers.web_post(), self.settings["cornerrow"], -1, low_corner=True, side=side),
                               self.helpers.left_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate1(-1, 0)), self.settings["cornerrow"], -1,
                                              low_corner=True, side=side),
                               self.helpers.key_place(self.helpers.web_post_bl(), 0, self.settings["cornerrow"]),
                               self.ml_place(self.thumb_post_tl()),
                           ]
                       )])

        shape = self.helpers.union([shape,
                       self.helpers.hull_from_shapes(
                           [
                               self.bl_place(self.thumb_post_tr()),
                               self.bl_place(self.helpers.translate(self.thumb_post_tr(), self.helpers.wall_locate1(-0.3, 1))),
                               self.bl_place(self.helpers.translate(self.thumb_post_tr(), self.helpers.wall_locate2(-0.3, 1))),
                               self.bl_place(self.helpers.translate(self.thumb_post_tr(), self.helpers.wall_locate3(-0.3, 1))),
                               self.ml_place(self.thumb_post_tl()),
                           ]
                       )])

        return shape

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array([-48, -37, 0]))
        position[2] = 0

        return position
