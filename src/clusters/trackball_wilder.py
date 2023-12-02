from clusters.trackball_orbyl import TrackballOrbyl
import json
import os
import logging
import numpy as np
from utils import plate

logger = logging.getLogger()

class TrackballWild(TrackballOrbyl):
    key_to_thumb_rotation = [] # may no longer be used?
    post_offsets = [
            [14, -8, 3],
            [3, -9, -7],
            [-4, 4, -6],
            [-5, 18, 19]
        ]

    tl_off = 1.7

    wall_offsets = [
        [
            -1.0,
            1.0,
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

    name = "TRACKBALL_WILD"


    def get_config(self):
        with open(os.path.join("src", "clusters", "json", "TRACKBALL_WILD.json"), mode='r') as fid:
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
        shift = [-.9*self.key_diameter/2+27-42, -.1*self.key_diameter/2+3-20, -5]
        for i in range(len(pos)):
            pos[i] = pos[i] + shift[i] + self.translation_offset[i]

        for i in range(len(rot)):
            rot[i] = rot[i] + self.rotation_offset[i]

        return pos, rot


    def tl_wall(self, shape):
        return self.helper.translate(self.tl_place(shape), self.wall_offsets[0])

    def mr_wall(self, shape):
        return self.helper.translate(self.mr_place(shape), self.wall_offsets[1])

    def br_wall(self, shape):
        return self.helper.translate(self.br_place(shape), self.wall_offsets[2])

    def bl_wall(self, shape):
        return self.helper.translate(self.bl_place(shape), self.wall_offsets[3])

    def tl_place(self, shape):
        shape = self.helper.rotate(shape, [0, 0, 0])
        t_off = self.key_translation_offsets[0]
        shape = self.helper.rotate(shape, self.key_rotation_offsets[0])
        shape = self.helper.translate(shape, (t_off[0], t_off[1]+self.key_diameter/2, t_off[2]))
        shape = self.helper.rotate(shape, [0, 0, -80])
        shape = self.track_place(shape)

        return shape

    def mr_place(self, shape):
        shape = self.helper.rotate(shape, [0, 0, 0])
        shape = self.helper.rotate(shape, self.key_rotation_offsets[1])
        t_off = self.key_translation_offsets[1]
        shape = self.helper.translate(shape, (t_off[0], t_off[1]+self.key_diameter/2, t_off[2]))
        shape = self.helper.rotate(shape, [0, 0, -150])
        shape = self.track_place(shape)

        return shape

    def br_place(self, shape):
        shape = self.helper.rotate(shape, [0, 0, 180])
        shape = self.helper.rotate(shape, self.key_rotation_offsets[2])
        t_off = self.key_translation_offsets[2]
        shape = self.helper.translate(shape, (t_off[0], t_off[1]+self.key_diameter/2, t_off[2]))
        shape = self.helper.rotate(shape, [0, 0, -195])
        shape = self.track_place(shape)

        return shape

    def bl_place(self, shape):
        logger.debug('thumb_bl_place()')
        shape = self.helper.rotate(shape, [0, 0, 180])
        shape = self.helper.rotate(shape, self.key_rotation_offsets[3])
        t_off = self.key_translation_offsets[3]
        shape = self.helper.translate(shape, (t_off[0], t_off[1]+self.key_diameter/2, t_off[2]))
        shape = self.helper.rotate(shape, [0, 0, -240])
        shape = self.track_place(shape)

        return shape


    def thumb_connectors(self, side="right"):
        print('thumb_connectors()')
        hulls = []

        # bottom 2 to tb
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.track_place(self.tb_post_l()),
                    self.bl_place(self.connector.web_post_tl()),
                    self.track_place(self.tb_post_bl()),
                    self.bl_place(self.connector.web_post_tr()),
                    self.br_place(self.connector.web_post_tl()),
                    self.track_place(self.tb_post_bl()),
                    self.br_place(self.connector.web_post_tr()),
                    self.track_place(self.tb_post_br()),
                    self.br_place(self.connector.web_post_tr()),
                    self.track_place(self.tb_post_br()),
                    self.mr_place(self.connector.web_post_br()),
                    self.track_place(self.tb_post_r()),
                    self.mr_place(self.connector.web_post_bl()),
                    self.tl_place(self.connector.web_post_br( )),
                    self.track_place(self.tb_post_r()),
                    self.tl_place(self.connector.web_post_bl( )),
                    self.track_place(self.tb_post_tr()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.track_place(self.tb_post_tl()),
                ]
            )
        )

        # bottom left
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.bl_place(self.connector.web_post_tr()),
                    self.br_place(self.connector.web_post_tl()),
                    self.bl_place(self.connector.web_post_br()),
                    self.br_place(self.connector.web_post_bl()),
                ]
            )
        )

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
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off)),
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

    # todo update walls for wild track, still identical to orbyl
    def walls(self, side="right"):
        print('thumb_walls()')
        # thumb, self.wallbuilder.walls
        shape = self.wallbuilder.wall_brace(
            self.mr_place, .5, 1, self.connector.web_post_tl(),
            (lambda sh: self.capbuilder.cluster_key_place(sh, 3, self.settings["lastrow"])), 0, -1, self.connector.web_post_bl(),
        )
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.mr_place, .5, 1, self.connector.web_post_tl(),
            self.mr_place, .5, 1, self.connector.web_post_tr(),
        )])
        # BOTTOM FRONT BETWEEN MR AND BR
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.mr_place, .5, 1, self.connector.web_post_tr(),
            self.br_place, 0, -1, self.connector.web_post_br(),
        )])
        # BOTTOM FRONT AT BR
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.br_place, 0, -1, self.connector.web_post_br(),
            self.br_place, 0, -1, self.connector.web_post_bl(),
        )])
        # BOTTOM FRONT BETWEEN BR AND BL
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.br_place, 0, -1, self.connector.web_post_bl(),
            self.bl_place, 0, -1, self.connector.web_post_br(),
        )])
        # BOTTOM FRONT AT BL
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.bl_place, 0, -1, self.connector.web_post_br(),
            self.bl_place, -1, -1, self.connector.web_post_bl(),
        )])
        # TOP LEFT BEHIND TRACKBALL
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.track_place, -1.5, 0, self.tb_post_tl(),
            (lambda sh: self.capbuilder.left_cluster_key_place(sh, self.settings["lastrow"] - 1, -1, side=self.settings["ball_side"], low_corner=True)), -1, 0, self.connector.web_post(),
        )])
        # LEFT OF TRACKBALL
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.track_place, -2, 0, self.tb_post_tl(),
            self.track_place, -2, 0, self.tb_post_l(),
        )])
        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.track_place, -2, 0, self.tb_post_l(),
            self.bl_place, -1, 0, self.connector.web_post_tl(),
        )])

        # BEFORE BTUS
        #
        # # LEFT OF TRACKBALL
        # shape = self.helper.union([shape, self.wallbuilder.wall_brace(
        #     self.track_place, -1.5, 0, self.tb_post_tl(),
        #     self.track_place, -1, 0, self.tb_post_l(),
        # )])
        # shape = self.helper.union([shape, self.wallbuilder.wall_brace(
        #     self.track_place, -1, 0, self.tb_post_l(),
        #     self.bl_place, -1, 0, self.connector.web_post_tl(),
        # )])

        shape = self.helper.union([shape, self.wallbuilder.wall_brace(
            self.bl_place, -1, 0, self.connector.web_post_tl(),
            self.bl_place, -1, -1, self.connector.web_post_bl(),
        )])

        return shape

    def connection(self, side='right'):

        print('thumb_connection()')
        # clunky bit on the top left thumb connection  (normal connectors don't work well)
        hulls = []

        # ======= These four account for offset between plate and wall methods
        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off)),
                    self.tl_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_tl())
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    self.tl_place(self.connector.web_post_bl()),
                    self.tl_place(self.connector.web_post_tl())
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tr()),
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off)),
                    self.tl_place(self.connector.web_post_br()),
                    self.tl_place(self.connector.web_post_tr())
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_br()),
                    self.tl_place(self.connector.web_post_br()),
                    self.tl_place(self.connector.web_post_bl()),
                    self.tl_place(self.connector.web_post_br())
                ]
            )
        )

        #  ==========================

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.capbuilder.left_cluster_key_place(self.connector.web_post(), self.settings["lastrow"] - 1, -1, side=side, low_corner=True),
                    # self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True),
                    self.track_place(self.tb_post_tl()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                    self.capbuilder.left_cluster_key_place(self.connector.web_post(), self.settings["lastrow"] - 1, -1, side=side, low_corner=True),
                    # self.capbuilder.left_cluster_key_place(self.helper.translate(self.connector.web_post(), wall_locate1(-1, 0)), self.settings["cornerrow"], -1, low_corner=True),
                    self.track_place(self.tb_post_tl()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),  # col 0 bottom, bottom left (at left side/edge)
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),  # top cluster self.capbuilder.key, bottom left (sort of top left)
                    self.tl_place(self.connector.web_post_bl()),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),  # col 1 bottom, bottom left
                    # self.tl_place(self.connector.web_post_tl(off_w=self.tl_off, off_h=self.tl_off))
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),  # col 0 bottom, bottom left (at left side/edge)
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 0, self.settings["cornerrow"]),
                    # self.tl_place(self.connector.web_post_bl(off_w=self.tl_off, off_h=self.tl_off)),  # top cluster self.capbuilder.key, bottom left (sort of top left)
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),  # col 1 bottom, bottom left
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off))
                ]
            )
        )

        # plates to columns 1 and 2
        hulls.append(
            self.helper.triangle_hulls(
                [
                    # self.tl_place(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),  # col 1 bottom, bottom right corner
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),  # col 1 bottom, bottom left corner
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    # self.tl_place(self.connector.web_post_tr()),
                    # self.tl_place(self.connector.web_post_tl()),
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 1, self.settings["cornerrow"]),  # col 1 bottom, bottom right corner
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),  # col 1 bottom, bottom left corner
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off))
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),  # col 2 bottom, bottom left corner
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off))
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_tl(), 2, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 1, self.settings["cornerrow"]),  # col 2 bottom, bottom left corner
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off))
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off)),  # col 2 bottom, bottom left corner
                    self.tl_place(self.connector.web_post_tl(off_h=self.tl_off))
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 2, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off))  # col 2 bottom, bottom left corner
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_br(), 2, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off))  # col 2 bottom, bottom left corner
                ]
            )
        )

        hulls.append(
            self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.mr_wall(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off))  # col 2 bottom, bottom left corner
                ]
            )
        )

        # Duplicate of above, just offset by x: -0.5 to ensure wall thickness
        hulls.append(
            self.helper.translate(self.helper.triangle_hulls(
                [
                    self.tl_place(self.connector.web_post_tr( off_h=self.tl_off)),
                    self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 3, self.settings["lastrow"]),  # col 2 bottom, top left corner
                    self.mr_wall(self.connector.web_post_tl()),
                    self.tl_place(self.connector.web_post_tr(off_h=self.tl_off))  # col 2 bottom, bottom left corner
                ]
            ), [-0.5, 0, 0])
        )

        # hulls.append(
        #     self.helper.triangle_hulls(
        #         [
        #             self.mr_wall(self.connector.web_post_tr()),
        #             self.mr_wall(self.connector.web_post_tl()),
        #             self.helper.translate(self.mr_wall(self.connector.web_post_tl()), [14, 15, -2]),
        #             self.mr_wall(self.connector.web_post_tr()),
        #         ]
        #     )
        # )
        #
        # # Duplicate of above, just offset by x: -0.5 to ensure wall thickness
        # hulls.append(
        #     self.helper.translate(self.helper.triangle_hulls(
        #         [
        #             self.mr_wall(self.connector.web_post_tr()),
        #             self.mr_wall(self.connector.web_post_tl()),
        #             self.helper.translate(self.mr_wall(self.connector.web_post_tl()), [14, 15, -2]),
        #             self.mr_wall(self.connector.web_post_tr()),
        #         ]
        #     ), [-0.5, 0, 0])
        # )


        hulls.append(
            self.helper.triangle_hulls(
                [
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
                self.capbuilder.cluster_key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                self.capbuilder.key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]),
                # self.capbuilder.left_cluster_key_place(self.connector.web_post_bl(), self.settings["cornerrow"], 0, low_corner=False, side=side),
                self.helper.translate(self.capbuilder.key_place(self.connector.web_post_bl(), 0, self.settings["cornerrow"]), wall_locate1(-1, 0))

            ]
        ))

        shape = self.helper.union(hulls)
        return shape

    def get_extras(self, shape, pos):
        posts = [shape]
        all_pos = []
        for i in range(len(pos)):
            all_pos.append(pos[i] + self.settings["tb_socket_translation_offset"][i])
        z_pos = abs(pos[2])
        for post_offset in self.post_offsets:
            support_z = z_pos + post_offset[2]
            new_offsets = post_offset.copy()
            new_offsets[2] = -z_pos
            support = self.helper.cylinder(1.5, support_z, 10)
            support = self.helper.translate(support, all_pos)
            support = self.helper.translate(support, new_offsets)
            base = self.helper.cylinder(4, 1, 10)
            new_offsets[2] = 0.5 - all_pos[2]
            base = self.helper.translate(base, all_pos)
            base = self.helper.translate(base, new_offsets)
            posts.append(base)
            support = self.helper.union([support, base])
            posts.append(support)
        return self.helper.union(posts)
