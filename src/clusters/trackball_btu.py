from clusters.trackball_wilder import TrackballWild
import json
import os
import logging

logger = logging.getLogger()

class TrackballBTU(TrackballWild):

    post_offsets = [
            [14, 0, -2],
            [1, -12, -7],
            [-11, 0, -10],
            [-1, 15, 0]
        ]

    name = "TRACKBALL_BTU"

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

    def has_btus(self):
        return True

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
