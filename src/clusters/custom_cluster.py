from clusters.default_cluster import DefaultCluster
import json
import os
import logging
import numpy as np
from utils import plate

logger = logging.getLogger()

class CustomCluster(DefaultCluster):
    name = "CUSTOM"
    num_keys = 7

    def get_config(self):
        with open(os.path.join("src", "clusters", "json", "CUSTOM.json"), mode='r') as fid:
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

    def tl_place(self, shape):
        logger.debug('tl_place()')
        shape = self.helper.rotate(shape, [9.5, -12, 10])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-32.5, -17.5, -2.5])
        return shape

    def tr_place(self, shape):
        logger.debug('tr_place()')
        shape = self.helper.rotate(shape, [10, -9, 10])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-12, -16, 1])
        return shape

    def mr_place(self, shape):
        logger.debug('mr_place()')
        shape = self.helper.rotate(shape, [-6, -28, 48])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-29, -40, -9])
        return shape

    def ml_place(self, shape):
        logger.debug('ml_place()')
        shape = self.helper.rotate(shape, [6, -28, 45])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-49, -27, -8])
        return shape

    def br_place(self, shape):
        logger.debug('br_place()')
        shape = self.helper.rotate(shape, [-16, -27, 54])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-37.8, -55.3, -19.3])
        return shape

    def bl_place(self, shape):
        logger.debug('bl_place()')
        shape = self.helper.rotate(shape, [-4, -29, 52])
        shape = self.helper.translate(shape, self.thumborigin())
        shape = self.helper.translate(shape, [-56.3, -43.3, -18.5])
        return shape

    def thumb_1x_layout(self, shape, cap=False):
        logger.debug('thumb_1x_layout()')
        if cap:
            shape_list = [
                self.mr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
                self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
                self.br_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
                self.bl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
                self.tr_place(self.helper.rotate(self.helper.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])),
                self.tl_place(self.helper.rotate(self.helper.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tl_rotation]))
            ]

            # if default_1U_cluster:
            #     # shape_list.append(self.tr_place(self.helper.rotate(self.helper.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
            #     shape_list.append(self.tr_place(self.helper.rotate(self.helper.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tr_rotation])))
            #     shape_list.append(self.tl_place(self.helper.rotate(self.helper.rotate(shape, (0, 0, 90)), [0, 0, self.thumb_plate_tl_rotation])))
            shapes = self.helper.add(shape_list)

        else:
            shape_list = [
                self.mr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_mr_rotation])),
                self.ml_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_ml_rotation])),
                self.br_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_br_rotation])),
                self.bl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_bl_rotation])),
                self.tr_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tr_rotation])),
                self.tl_place(self.helper.rotate(shape, [0, 0, self.thumb_plate_tl_rotation]))
            ]

            shapes = self.helper.union(shape_list)
        return shapes

    def thumbcaps(self, side='right'):
        t1 = self.thumb_1x_layout(self.capbuilder.sa_cap(1), cap=True)
        if not self.settings["default_1U_cluster"]:
            t1.add(self.thumb_15x_layout(self.capbuilder.sa_cap(1), cap=True))
        return t1

    def thumb(self, side="right"):
        print('thumb()')
        shape = self.thumb_1x_layout(self.helper.rotate(plate.single_plate(self.settings, self.helper, side=side), (0, 0, -90)))

        return shape

    def thumb_post_tr(self):
        logger.debug('thumb_post_tr()')
        return self.helper.translate(self.connector.web_post(),
                         [(self.settings["mount_width"] / 2) - self.settings["post_adj"], ((self.settings["mount_height"] / 2)) - self.settings["post_adj"], 0]
                         )

    def thumb_post_tl(self):
        logger.debug('thumb_post_tl()')
        return self.helper.translate(self.connector.web_post(),
                         [-(self.settings["mount_width"] / 2) + self.settings["post_adj"], ((self.settings["mount_height"] / 2)) - self.settings["post_adj"], 0]
                         )

    def thumb_post_bl(self):
        logger.debug('thumb_post_bl()')
        return self.helper.translate(self.connector.web_post(),
                         [-(self.settings["mount_width"] / 2) + self.settings["post_adj"], -((self.settings["mount_height"] / 2)) + self.settings["post_adj"], 0]
                         )

    def thumb_post_br(self):
        logger.debug('thumb_post_br()')
        return self.helper.translate(self.connector.web_post(),
                         [(self.settings["mount_width"] / 2) - self.settings["post_adj"], -((self.settings["mount_height"] / 2)) + self.settings["post_adj"], 0]
                         )
