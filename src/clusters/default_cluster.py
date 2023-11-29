import json
import os
import numpy as np


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
                print(f"{self.name}: NO MEMBER VARIABLE FOR " + str(item))
                continue
            setattr(self, str(item), data[item])
        return data

    def __init__(self, settings: dict, helpers):
        self.get_config()
        print(f"{self.name} built")
        self.settings = settings
        self.helpers = helpers

    def thumborigin(self):
        # debugprint('thumborigin()')
        origin = self.helpers.key_position([mount_width / 2, -(mount_height / 2), 0], 1, cornerrow)
        _thumb_offsets = self.thumb_offsets.copy()
        if self.settings["shift_column"] != 0:
            _thumb_offsets[0] = self.thumb_offsets[0] + (self.settings["shift_column"] * (mount_width + 6))
            # if shift_column < 0:  # raise cluster up when moving inward
            #     _thumb_offsets[1] = self.thumb_offsets[1] - (shift_column * 3)
            #     _thumb_offsets[2] = self.thumb_offsets[2] - (shift_column * 8)
            #     if shift_column <= -2:
            #         # y = shift_column * 15
            #         _thumb_offsets[1] = self.thumb_offsets[1] - (shift_column * 15)
        for i in range(len(origin)):
            origin[i] = origin[i] + _thumb_offsets[i]

        return origin

    def thumb_rotate(self):
        x = y = z = 0
        if self.settings["shift_column"] != 0:
            y = self.settings["shift_column"] * 8
            if self.settings["shift_column"] < 0:
                z = self.settings["shift_column"] * -10
        return [x, y, z]

    def thumb_place(self, shape):
        shape = self.helpers.translate(shape, self.thumborigin())
        return self.helpers.rotate(shape, self.thumb_rotate())

    def tl_place(self, shape):
        debugprint('tl_place()')
        shape = self.helpers.rotate(shape, [7.5, -18, 10])
        shape = self.helpers.translate(shape, [-32.5, -14.5, -2.5])
        shape = self.thumb_place(shape)
        return shape

    def tr_place(self, shape):
        debugprint('tr_place()')
        shape = self.helpers.rotate(shape, [10, -15, 10])
        shape = self.helpers.translate(shape, [-12, -16, 3])
        shape = self.thumb_place(shape)
        return shape

    def mr_place(self, shape):
        debugprint('mr_place()')
        shape = self.helpers.rotate(shape, [-6, -34, 48])
        shape = self.helpers.translate(shape, [-29, -40, -13])
        shape = self.thumb_place(shape)
        return shape

    def ml_place(self, shape):
        debugprint('ml_place()')
        shape = self.helpers.rotate(shape, [6, -34, 40])
        shape = self.helpers.translate(shape, [-51, -25, -12])
        shape = self.thumb_place(shape)
        return shape

    def br_place(self, shape):
        debugprint('br_place()')
        shape = self.helpers.rotate(shape, [-16, -33, 54])
        shape = self.helpers.translate(shape, [-37.8, -55.3, -25.3])
        shape = self.thumb_place(shape)
        return shape

    def bl_place(self, shape):
        debugprint('bl_place()')
        shape = self.helpers.rotate(shape, [-4, -35, 52])
        shape = self.helpers.translate(shape, [-56.3, -43.3, -23.5])
        shape = self.thumb_place(shape)
        return shape

    def thumb_1x_layout(self, shape, cap=False):
        debugprint('thumb_1x_layout()')
        if cap:
            shape_list = [
                self.mr_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
                self.ml_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
                self.br_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
                self.bl_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            ]

            if default_1U_cluster:
                shape_list.append(self.tr_place(self.helpers.rotate(self.helpers.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
                shape_list.append(self.tr_place(self.helpers.rotate(self.helpers.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
                shape_list.append(self.tl_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_tl_rotation])))
            shapes = self.helpers.add(shape_list)

        else:
            shape_list = [
                self.mr_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
                self.ml_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
                self.br_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
                self.bl_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            ]
            if default_1U_cluster:
                shape_list.append(self.tr_place(self.helpers.rotate(self.helpers.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
            shapes = self.helpers.union(shape_list)
        return shapes

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        debugprint('thumb_15x_layout()')
        if plate:
            if cap:
                shape = self.helpers.rotate(shape, (0, 0, 90))
                cap_list = [self.tl_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_tl_rotation]))]
                cap_list.append(self.tr_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])))
                return self.helpers.add(cap_list)
            else:
                shape_list = [self.tl_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_tl_rotation]))]
                if not self.settings["default_1U_cluster"]:
                    shape_list.append(self.tr_place(self.helpers.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])))
                return self.helpers.union(shape_list)
        else:
            if cap:
                shape = self.helpers.rotate(shape, (0, 0, 90))
                shape_list = [
                    self.tl_place(shape),
                ]
                shape_list.append(self.tr_place(shape))

                return self.helpers.add(shape_list)
            else:
                shape_list = [
                    self.tl_place(shape),
                ]
                if not self.settings["default_1U_cluster"]:
                    shape_list.append(self.tr_place(shape))

                return union(shape_list)

    def thumbcaps(self, side='right'):
        t1 = self.thumb_1x_layout(self.helpers.sa_cap(1), cap=True)
        if not self.settings["default_1U_cluster"]:
            t1.add(self.thumb_15x_layout(self.helpers.sa_cap(1.5), cap=True))
        return t1

    def thumb(self, side="right"):
        print('thumb()')
        shape = self.thumb_1x_layout(self.helpers.rotate(self.helpers.single_plate(side=side), (0, 0, -90)))
        shape = self.helpers.union([shape, self.thumb_15x_layout(self.helpers.rotate(self.helpers.single_plate(side=side), (0, 0, -90)))])
        shape = self.helpers.union([shape, self.thumb_15x_layout(self.helpers.double_plate(), plate=False)])

        return shape

    def thumb_post_tr(self):
        debugprint('thumb_post_tr()')
        return self.helpers.translate(self.helpers.web_post(),
                         [(mount_width / 2) - post_adj, ((mount_height / 2) + double_plate_height) - post_adj, 0]
                         )

    def thumb_post_tl(self):
        debugprint('thumb_post_tl()')
        return self.helpers.translate(self.helpers.web_post(),
                         [-(mount_width / 2) + post_adj, ((mount_height / 2) + double_plate_height) - post_adj, 0]
                         )

    def thumb_post_bl(self):
        debugprint('thumb_post_bl()')
        return self.helpers.translate(self.helpers.web_post(),
                         [-(mount_width / 2) + post_adj, -((mount_height / 2) + double_plate_height) + post_adj, 0]
                         )

    def thumb_post_br(self):
        debugprint('thumb_post_br()')
        return self.helpers.translate(self.helpers.web_post(),
                         [(mount_width / 2) - post_adj, -((mount_height / 2) + double_plate_height) + post_adj, 0]
                         )

    def thumb_connectors(self, side="right"):
        print('default thumb_connectors()')
        hulls = []

        # Top two
        if self.settings["default_1U_cluster"]:
            hulls.append(
                self.helpers.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tr()),
                        self.tl_place(self.thumb_post_br()),
                        self.tr_place(self.helpers.web_post_tl()),
                        self.tr_place(self.helpers.web_post_bl()),
                    ]
                )
            )
        else:
            hulls.append(
                self.helpers.triangle_hulls(
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
                    self.br_place(self.helpers.web_post_tr()),
                    self.br_place(self.helpers.web_post_br()),
                    self.mr_place(self.helpers.web_post_tl()),
                    self.mr_place(self.helpers.web_post_bl()),
                ]
            )
        )
        # centers of the bottom four
        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.bl_place(self.helpers.web_post_tr()),
                    self.bl_place(self.helpers.web_post_br()),
                    self.ml_place(self.helpers.web_post_tl()),
                    self.ml_place(self.helpers.web_post_bl()),
                ]
            )
        )

        # top two to the middle two, starting on the left
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
                ]
            )
        )

        if self.settings["default_1U_cluster"]:
            hulls.append(
                self.helpers.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.ml_place(self.helpers.web_post_tr()),
                        self.tl_place(self.thumb_post_bl()),
                        self.ml_place(self.helpers.web_post_br()),
                        self.tl_place(self.thumb_post_br()),
                        self.mr_place(self.helpers.web_post_tr()),
                        self.tr_place(self.helpers.web_post_bl()),
                        self.mr_place(self.helpers.web_post_br()),
                        self.tr_place(self.helpers.web_post_br()),
                    ]
                )
            )
        else:
            # top two to the main keyboard, starting on the left
            hulls.append(
                self.helpers.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.ml_place(self.helpers.web_post_tr()),
                        self.tl_place(self.thumb_post_bl()),
                        self.ml_place(self.helpers.web_post_br()),
                        self.tl_place(self.thumb_post_br()),
                        self.mr_place(self.helpers.web_post_tr()),
                        self.tr_place(self.thumb_post_bl()),
                        self.mr_place(self.helpers.web_post_br()),
                        self.tr_place(self.thumb_post_br()),
                    ]
                )
            )

        if self.settings["default_1U_cluster"]:
            hulls.append(
                self.helpers.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 0, cornerrow),
                        self.tl_place(self.thumb_post_tr()),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 1, cornerrow),
                        self.tr_place(self.helpers.web_post_tl()),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 1, cornerrow),
                        self.tr_place(self.helpers.web_post_tr()),
                        self.helpers.cluster_key_place(self.helpers.web_post_br(), 1, cornerrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tl(), 2, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 2, lastrow),
                        self.tr_place(self.helpers.web_post_tr()),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 2, lastrow),
                        self.tr_place(self.helpers.web_post_br()),
                        self.helpers.cluster_key_place(self.helpers.web_post_br(), 2, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tr(), 2, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tl(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, cornerrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tr(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_br(), 3, cornerrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 4, cornerrow),
                    ]
                )
            )
        else:
            hulls.append(
                self.helpers.triangle_hulls(
                    [
                        self.tl_place(self.thumb_post_tl()),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 0, cornerrow),
                        self.tl_place(self.thumb_post_tr()),
                        self.helpers.cluster_key_place(self.helpers.web_post_br(), 0, cornerrow),
                        self.tr_place(self.thumb_post_tl()),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 1, cornerrow),
                        self.tr_place(self.thumb_post_tr()),
                        self.helpers.cluster_key_place(self.helpers.web_post_br(), 1, cornerrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tl(), 2, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 2, lastrow),
                        self.tr_place(self.thumb_post_tr()),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 2, lastrow),
                        self.tr_place(self.thumb_post_br()),
                        self.helpers.cluster_key_place(self.helpers.web_post_br(), 2, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tr(), 2, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tl(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, cornerrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tr(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_br(), 3, cornerrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 4, cornerrow),
                    ]
                )
            )

        hulls.append(
            self.helpers.triangle_hulls(
                [
                    self.helpers.cluster_key_place(self.helpers.web_post_br(), 1, cornerrow),
                    self.helpers.cluster_key_place(self.helpers.web_post_tl(), 2, lastrow),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 2, cornerrow),
                    self.helpers.cluster_key_place(self.helpers.web_post_tr(), 2, lastrow),
                    self.helpers.cluster_key_place(self.helpers.web_post_br(), 2, cornerrow),
                    self.helpers.cluster_key_place(self.helpers.web_post_bl(), 3, cornerrow),
                ]
            )
        )

        if not self.settings["full_last_rows"]:
            hulls.append(
                self.helpers.triangle_hulls(
                    [
                        self.helpers.cluster_key_place(self.helpers.web_post_tr(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_br(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_tr(), 3, lastrow),
                        self.helpers.cluster_key_place(self.helpers.web_post_bl(), 4, cornerrow),
                    ]
                )
            )

        return union(hulls)

    def walls(self, side="right"):
        print('thumb_walls()')
        # thumb, walls
        if self.settings["default_1U_cluster"]:
            shape = self.helpers.union([self.helpers.wall_brace(self.mr_place, 0, -1, self.helpers.web_post_br(), self.tr_place, 0, -1, self.helpers.web_post_br())])
        else:
            shape = self.helpers.union([self.helpers.wall_brace(self.mr_place, 0, -1, self.helpers.web_post_br(), self.tr_place, 0, -1, self.thumb_post_br())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.mr_place, 0, -1, self.helpers.web_post_br(), self.mr_place, 0, -1, self.helpers.web_post_bl())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.br_place, 0, -1, self.helpers.web_post_br(), self.br_place, 0, -1, self.helpers.web_post_bl())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.ml_place, -0.3, 1, self.helpers.web_post_tr(), self.ml_place, 0, 1, self.helpers.web_post_tl())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.bl_place, 0, 1, self.helpers.web_post_tr(), self.bl_place, 0, 1, self.helpers.web_post_tl())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.br_place, -1, 0, self.helpers.web_post_tl(), self.br_place, -1, 0, self.helpers.web_post_bl())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.bl_place, -1, 0, self.helpers.web_post_tl(), self.bl_place, -1, 0, self.helpers.web_post_bl())])
        # thumb, corners
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.br_place, -1, 0, self.helpers.web_post_bl(), self.br_place, 0, -1, self.helpers.web_post_bl())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.bl_place, -1, 0, self.helpers.web_post_tl(), self.bl_place, 0, 1, self.helpers.web_post_tl())])
        # thumb, tweeners
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.mr_place, 0, -1, self.helpers.web_post_bl(), self.br_place, 0, -1, self.helpers.web_post_br())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.ml_place, 0, 1, self.helpers.web_post_tl(), self.bl_place, 0, 1, self.helpers.web_post_tr())])
        shape = self.helpers.union([shape, self.helpers.wall_brace(self.bl_place, -1, 0, self.helpers.web_post_bl(), self.br_place, -1, 0, self.helpers.web_post_tl())])
        if self.settings["default_1U_cluster"]:
            shape = self.helpers.union([shape,
                           self.helpers.wall_brace(self.tr_place, 0, -1, self.helpers.web_post_br(), (lambda sh: self.helpers.cluster_key_place(sh, 3, lastrow)), 0,
                                      -1, self.helpers.web_post_bl())])
        else:
            shape = self.helpers.union([shape, self.helpers.wall_brace(self.tr_place, 0, -1, self.thumb_post_br(),
                                             (lambda sh: self.helpers.cluster_key_place(sh, 3, lastrow)), 0, -1, self.helpers.web_post_bl())])

        return shape

    def connection(self, side='right'):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        shape = self.helpers.union([self.helpers.bottom_hull(
            [
                self.helpers.left_cluster_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                self.helpers.left_cluster_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                self.ml_place(self.helpers.translate(self.helpers.web_post_tr(), self.helpers.wall_locate2(-0.3, 1))),
                self.ml_place(self.helpers.translate(self.helpers.web_post_tr(), self.helpers.wall_locate3(-0.3, 1))),
            ]
        )])

        shape = self.helpers.union([shape,
                       self.helpers.hull_from_shapes(
                           [
                               self.helpers.left_cluster_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate2(-1, 0)), cornerrow, -1,
                                              low_corner=True, side=side),
                               self.helpers.left_cluster_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate3(-1, 0)), cornerrow, -1,
                                              low_corner=True, side=side),
                               self.ml_place(self.helpers.translate(self.helpers.web_post_tr(), self.helpers.wall_locate2(-0.3, 1))),
                               self.ml_place(self.helpers.translate(self.helpers.web_post_tr(), self.helpers.wall_locate3(-0.3, 1))),
                               self.tl_place(self.thumb_post_tl()),
                           ]
                       )
                       ])  # )

        shape = self.helpers.union([shape, self.helpers.hull_from_shapes(
            [
                self.helpers.left_cluster_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                self.helpers.left_cluster_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate2(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                self.helpers.left_cluster_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate3(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.helpers.union([shape, self.helpers.hull_from_shapes(
            [
                self.helpers.left_cluster_key_place(self.helpers.web_post(), cornerrow, -1, low_corner=True, side=side),
                self.helpers.left_cluster_key_place(self.helpers.translate(self.helpers.web_post(), self.helpers.wall_locate1(-1, 0)), cornerrow, -1, low_corner=True, side=side),
                self.helpers.key_place(self.helpers.web_post_bl(), 0, cornerrow),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.helpers.union([shape, self.helpers.hull_from_shapes(
            [
                self.ml_place(self.helpers.web_post_tr()),
                self.ml_place(self.helpers.translate(self.helpers.web_post_tr(), self.helpers.wall_locate1(-0.3, 1))),
                self.ml_place(self.helpers.translate(self.helpers.web_post_tr(), self.helpers.wall_locate2(-0.3, 1))),
                self.ml_place(self.helpers.translate(self.helpers.web_post_tr(), self.helpers.wall_locate3(-0.3, 1))),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        shape = self.helpers.union([shape, self.helpers.hull_from_shapes(
            [
                self.tl_place(self.thumb_post_tl()),
                cluster_key_place(self.helpers.web_post_bl(), 0, cornerrow),
                self.helpers.key_place(self.helpers.web_post_bl(), 0, cornerrow),
                # self.helpers.left_cluster_key_place(self.helpers.web_post_bl(), cornerrow, 0, low_corner=False, side=side),
                self.helpers.translate(self.helpers.key_place(self.helpers.web_post_bl(), 0, cornerrow), self.helpers.wall_locate1(-1, 0)),
                self.tl_place(self.thumb_post_tl()),
            ]
        )])

        # shape = union([shape, key_place(sphere(5), 0, cornerrow)])

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
