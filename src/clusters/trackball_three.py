from clusters.default_cluster import DefaultCluster
import json
import os
import logging
import numpy as np
from utils import plate

logger = logging.getLogger()

class TrackballThree(DefaultCluster):
    num_keys = 4
    is_tb = True
    key_diameter = 75
    translation_offset = [
        0,
        0,
        10
    ]
    rotation_offset = [
        0,
        0,
        0
    ]
    key_translation_offsets = [
        [
            0.0,
            0.0,
            -8.0
        ],
        [
            0.0,
            0.0,
            -8.0
        ],
        [
            0.0,
            0.0,
            -8.0
        ],
        [
            0.0,
            0.0,
            -8.0
        ]
    ]
    key_rotation_offsets = [
        [
            0.0,
            0.0,
            0.0
        ],
        [
            0.0,
            0.0,
            0.0
        ],
        [
            0.0,
            0.0,
            0.0
        ],
        [
            0.0,
            0.0,
            0.0
        ]
    ]

    name = "TRACKBALL_THREE"

    def get_config(self):
        with open(os.path.join("src", "clusters", "json", "TRACKBALL_THREE.json"), mode='r') as fid:
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
        rot = [10, -15, 5]
        pos = self.thumborigin()
        # Changes size based on self.capbuilder.key diameter around ball, shifting off of the top left cluster key.
        shift = [-.9 * self.key_diameter/2 + 27 - 42, -.1 * self.key_diameter / 2 + 3 - 20, -5]
        for i in range(len(pos)):
            pos[i] = pos[i] + shift[i] + self.translation_offset[i]

        for i in range(len(rot)):
            rot[i] = rot[i] + self.rotation_offset[i]

        return pos, rot

    def track_place(self, shape):
        pos, rot = self.position_rotation()
        shape = self.helper.rotate(shape, rot)
        shape = self.helper.translate(shape, pos)
        return shape

    def tl_place(self, shape):
        shape = self.helper.rotate(shape, [0, 0, 0])
        t_off = self.key_translation_offsets[0]
        shape = self.helper.rotate(shape, self.key_rotation_offsets[0])
        shape = self.helper.translate(shape, (t_off[0], t_off[1] + self.key_diameter / 2, t_off[2]))
        shape = self.helper.rotate(shape, [0,0,-80])
        shape = self.track_place(shape)

        return shape

    def mr_place(self, shape):
        shape = self.helper.rotate(shape, [0, 0, 0])
        shape = self.helper.rotate(shape, self.key_rotation_offsets[1])
        t_off = self.key_translation_offsets[1]
        shape = self.helper.translate(shape, (t_off[0], t_off[1] + self.key_diameter/2, t_off[2]))
        shape = self.helper.rotate(shape, [0,0,-118])
        shape = self.track_place(shape)

        return shape

    def br_place(self, shape):
        shape = self.helper.rotate(shape, [0, 0, 180])
        shape = self.helper.rotate(shape, self.key_rotation_offsets[2])
        t_off = self.key_translation_offsets[2]
        shape = self.helper.translate(shape, (t_off[0], t_off[1]+self.key_diameter/2, t_off[2]))
        shape = self.helper.rotate(shape, [0,0,-180])
        shape = self.track_place(shape)

        return shape

    def bl_place(self, shape):
        logger.debug('thumb_bl_place()')
        shape = self.helper.rotate(shape, [0, 0, 180])
        shape = self.helper.rotate(shape, self.key_rotation_offsets[3])
        t_off = self.key_translation_offsets[3]
        shape = self.helper.translate(shape, (t_off[0], t_off[1]+self.key_diameter/2, t_off[2]))
        shape = self.helper.rotate(shape, [0,0,-230])
        shape = self.track_place(shape)

        return shape

    def thumb_1x_layout(self, shape, cap=False):
        logger.debug('thumb_1x_layout()')
        return self.helper.union([
            self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])),
            self.mr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
            # self.bl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
            # self.br_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
        ])

    def thumb_15x_layout(self, shape, cap=False, plate=True):
        return self.br_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_br_rotation]))

    def thumb_fx_layout(self, shape):
        return self.helper.union([])

    def thumbcaps(self, side='right'):
        t1 = self.thumb_1x_layout(self.capbuilder.sa_cap(1), cap=True)
        if not self.settings["default_1U_cluster"]:
            t1.add(self.thumb_15x_layout(self.helper.rotate(self.capbuilder.sa_cap(2), (0, 0, 90)), cap=True))
        return t1


    def tb_post_r(self):
        logger.debug('post_r()')
        radius = self.settings["ball_diameter"]/2 + self.settings["ball_wall_thickness"] + self.settings["ball_gap"]
        return self.helper.translate(self.connector.web_post(),
                         [1.0*(radius - self.settings["post_adj"]), 0.0*(radius - self.settings["post_adj"]), 0]
                         )

    def tb_post_tr(self):
        logger.debug('post_tr()')
        radius = self.settings["ball_diameter"]/2+self.settings["ball_wall_thickness"] + self.settings["ball_gap"]
        return self.helper.translate(self.connector.web_post(),
                         [0.5*(radius - self.settings["post_adj"]), 0.866*(radius - self.settings["post_adj"]), 0]
                         )


    def tb_post_tl(self):
        logger.debug('post_tl()')
        radius = self.settings["ball_diameter"]/2+self.settings["ball_wall_thickness"] + self.settings["ball_gap"]
        return self.helper.translate(self.connector.web_post(),
                         [-0.5*(radius - self.settings["post_adj"]), 0.866*(radius - self.settings["post_adj"]), 0]
                         )


    def tb_post_l(self):
        logger.debug('post_l()')
        radius = self.settings["ball_diameter"]/2+self.settings["ball_wall_thickness"] + self.settings["ball_gap"]
        return self.helper.translate(self.connector.web_post(),
                         [-1.0*(radius - self.settings["post_adj"]), 0.0*(radius - self.settings["post_adj"]), 0]
                         )

    def tb_post_bl(self):
        logger.debug('post_bl()')
        radius = self.settings["ball_diameter"]/2+self.settings["ball_wall_thickness"] + self.settings["ball_gap"]
        return self.helper.translate(self.connector.web_post(),
                         [-0.5*(radius - self.settings["post_adj"]), -0.866*(radius - self.settings["post_adj"]), 0]
                         )


    def tb_post_br(self):
        logger.debug('post_br()')
        radius = self.settings["ball_diameter"]/2+self.settings["ball_wall_thickness"] + self.settings["ball_gap"]
        return self.helper.translate(self.connector.web_post(),
                         [0.5*(radius - self.settings["post_adj"]), -0.866*(radius - self.settings["post_adj"]), 0]
                         )

    # def thumb(self, side="right"):
    #     print('thumb()')
    #     shape = self.thumb_fx_layout(self.helper.rotate(single_plate(side=side), [0.0, 0.0, -90]))
    #     shape = self.helper.union([shape, self.thumb_fx_layout(double_plate())])
    #     shape = self.helper.union([shape, self.thumb_1x_layout(single_plate(side=side))])
    #
    #     # shape = self.helper.union([shape, trackball_layout(trackball_socket())])
    #     # shape = self.1x_layout(single_plate(side=side))
    #     return shape

    def thumb(self, side="right"):
        print('thumb()')
        shape = self.thumb_1x_layout(self.helper.rotate(plate.single_plate(self.settings, self.helper, side=side), (0, 0, -90)))
        shape = self.helper.union([shape, self.thumb_15x_layout(self.helper.rotate(plate.single_plate(self.settings, self.helper, side=side), (0, 0, -90)))])
        # shape = self.helper.union([shape, self.thumb_15x_layout(self.helper.rotate(double_plate(), (0, 0, -90)))])
        # shape = self.helper.union([shape, self.thumb_15x_layout(double_plate(), plate=False)])

        return shape

    def thumb_connectors(self, side="right"):
        print('thumb_connectors()')
        hulls = []

        # bottom 2 to tb
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.track_place(self.tb_post_l()),
                    self.br_place(self.connector.web_post_tl()),
                    self.track_place(self.tb_post_bl()),
                    self.br_place(self.connector.web_post_tr()),
                    self.br_place(self.connector.web_post_tl()),
                    self.track_place(self.tb_post_bl()),
                    self.br_place(self.connector.web_post_tr()),
                    self.track_place(self.tb_post_br()),
                    self.br_place(self.connector.web_post_tr()),
                    self.track_place(self.tb_post_br()),
                    self.mr_place(self.connector.web_post_br()),
                    self.track_place(self.tb_post_r()),
                    self.mr_place(self.connector.web_post_bl()),
                    self.tl_place(self.connector.web_post_br()),
                    self.track_place(self.tb_post_r()),
                    self.tl_place(self.connector.web_post_bl()),
                    self.track_place(self.tb_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.track_place(self.tb_post_tl()),
                ]
            )
        )

        # bottom left
        # hulls.append(
        #     self.helper.triangle_hulls(
        #         [
        #             self.bl_place(self.connector.web_post_tr()),
        #             self.br_place(self.connector.web_post_tl()),
        #             self.bl_place(self.connector.web_post_br()),
        #             self.br_place(self.connector.web_post_bl()),
        #         ]
        #     )
        # )

        # bottom right
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.br_place(self.connector.web_post_tr()),
                    self.mr_place(self.connector.web_post_br()),
                    self.br_place(self.connector.web_post_br()),
                    self.mr_place(self.connector.web_post_tr()),
                ]
            )
        )
        # top right
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.mr_place(self.connector.web_post_bl()),
                    self.tl_place(self.connector.web_post_br()),
                    self.mr_place(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_tr()),
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

        return self.helper.union(hulls)

    def walls(self, side="right"):
        print('thumb_walls()')
        # thumb, self.wallbuilder.walls
        shape = self.wallbuilder.wall_brace(
            self.mr_place, .5, 1, self.connector.web_post_tr(),
            (lambda sh: self.capbuilder.cluster_key_place(sh, 3, self.settings["lastrow"])), 0, -1, self.connector.web_post_bl(),
        )
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.mr_place, .5, 1, self.connector.web_post_tr(),
            self.br_place, 0, -1, self.connector.web_post_br(),
        )])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.br_place, 0, -1, self.connector.web_post_br(),
            self.br_place, 0, -1, self.connector.web_post_bl(),
        )])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.br_place, 0, -1, self.connector.web_post_bl(),
            # self.bl_place, 0, -1, self.connector.web_post_br(),
            self.br_place, -2, -1, self.connector.web_post_bl(),
        )])
        # shape = self.helper.union([shape, self.wallbuilder.wall_brace(
        #     self.bl_place, 0, -1, self.connector.web_post_br(),
        #     self.bl_place, -1, -1, self.connector.web_post_bl(),
        # )])

        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.track_place, -1.5, 0, self.tb_post_tl(),
            (lambda sh: self.capbuilder.left_cluster_key_place(sh, self.settings["lastrow"] - 1, -1, side=self.settings["ball_side"], low_corner=True)), -1, 0, self.connector.web_post(),
        )])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.track_place, -1.5, 0, self.tb_post_tl(),
            self.track_place, -1, 0, self.tb_post_l(),
        )])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.track_place, -1, 0, self.tb_post_l(),
            self.br_place, -2, 0, self.connector.web_post_tl(),
        )])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.br_place, -2, 0, self.connector.web_post_tl(),
            self.br_place, -2, -1, self.connector.web_post_bl(),
        )])

        return shape

    def connection(self, side='right'):
        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        hulls = []
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.capbuilder.left_cluster_key_place(self.connector.web_post(), self.settings["lastrow"] - 1, -1, side=side, low_corner=True),                # left_cluster_key_place(self.helper.translate(self.connector.web_post(), wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True),
                    self.track_place(self.tb_post_tl()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.tl_place(self.connector.web_post_bl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 0, self.settings["cornerrow"]),
                    self.tl_place(self.connector.web_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),
                    self.tl_place(self.connector.web_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),
                    self.tl_place(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                    self.tl_place(self.connector.web_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),
                    self.mr_place(self.connector.web_post_tl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),
                    self.mr_place(self.connector.web_post_tr()),
                    self.mr_place(self.connector.web_post_tl()),
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
        shape = self.helper.union(hulls)
        return shape

    def has_btus(self):
        return False

    def screw_positions(self):
        position = self.thumborigin()
        position = list(np.array(position) + np.array([-72, -35, -16]))
        position[2] = 0

        return position
