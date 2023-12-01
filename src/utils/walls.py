import logging

from utils import connectors

logger = logging.getLogger()


class WallBuilder():

    def __init__(self, settings, helper, capbuilder, connector = None) -> None:
        self.settings = settings
        self.helper = helper
        self.capbuilder = capbuilder
        if connector:
            self.connector = connector
        else:
            self.connector = connectors.WebConnector(self.settings, self.helper, self.capbuilder)

    def is_side(self, side, param):
        return param == side or param == "both"
    

    def wall_locate1(self, dx, dy):
        logger.debug("wall_locate1()")
        return [dx * self.settings["wall_thickness"], dy * self.settings["wall_thickness"], -1]


    def wall_locate2(self, dx, dy):
        logger.debug("wall_locate2()")
        return [dx * self.settings["wall_x_offset"], dy * self.settings["wall_y_offset"], -self.settings["wall_z_offset"]]


    def wall_locate3(self, dx, dy, back=False):
        logger.debug("wall_locate3()")
        if back:
            return [
                dx * (self.settings["wall_x_offset"] + self.settings["wall_base_x_thickness"]),
                dy * (self.settings["wall_y_offset"] + self.settings["wall_base_back_thickness"]),
                -self.settings["wall_z_offset"],
            ]
        else:
            return [
                dx * (self.settings["wall_x_offset"] + self.settings["wall_base_x_thickness"]),
                dy * (self.settings["wall_y_offset"] + self.settings["wall_base_y_thickness"]),
                -self.settings["wall_z_offset"],
            ]
        # return [
        #     dx * (wall_xy_offset + wall_thickness),
        #     dy * (wall_xy_offset + wall_thickness),
        #     -wall_z_offset,
        # ]


    def wall_brace(self, place1, dx1, dy1, post1, place2, dx2, dy2, post2, back=False):
        logger.debug("wall_brace()")
        hulls = []

        hulls.append(place1(post1))
        hulls.append(place1(self.helper.translate(post1, self.wall_locate1(dx1, dy1))))
        hulls.append(place1(self.helper.translate(post1, self.wall_locate2(dx1, dy1))))
        hulls.append(place1(self.helper.translate(post1, self.wall_locate3(dx1, dy1, back))))

        hulls.append(place2(post2))
        hulls.append(place2(self.helper.translate(post2, self.wall_locate1(dx2, dy2))))
        hulls.append(place2(self.helper.translate(post2, self.wall_locate1(dx2, dy2))))
        hulls.append(place2(self.helper.translate(post2, self.wall_locate2(dx2, dy2))))
        hulls.append(place2(self.helper.translate(post2, self.wall_locate3(dx2, dy2, back))))
        shape1 = self.helper.hull_from_shapes(hulls)

        hulls = []
        hulls.append(place1(self.helper.translate(post1, self.wall_locate2(dx1, dy1))))
        hulls.append(place1(self.helper.translate(post1, self.wall_locate3(dx1, dy1, back))))
        hulls.append(place2(self.helper.translate(post2, self.wall_locate2(dx2, dy2))))
        hulls.append(place2(self.helper.translate(post2, self.wall_locate3(dx2, dy2, back))))
        shape2 = self.helper.bottom_hull(hulls)

        return self.helper.union([shape1, shape2])
        # return shape1


    def key_wall_brace(self, x1, y1, dx1, dy1, post1, x2, y2, dx2, dy2, post2, back=False):
        logger.debug("key_wall_brace()")
        return self.wall_brace(
            (lambda shape: self.capbuilder.key_place(shape, x1, y1)),
            dx1,
            dy1,
            post1,
            (lambda shape: self.capbuilder.key_place(shape, x2, y2)),
            dx2,
            dy2,
            post2,
            back
        )


    def back_wall(self):
        logger.debug("back_wall()")
        x = 0
        shape = self.helper.union([self.key_wall_brace(x, 0, 0, 1, self.connector.web_post_tl(), x, 0, 0, 1, self.connector.web_post_tr(), back=True)])
        for i in range(self.settings["ncols"] - 1):
            x = i + 1
            shape = self.helper.union([shape, self.key_wall_brace(x, 0, 0, 1, self.connector.web_post_tl(), x, 0, 0, 1, self.connector.web_post_tr(), back=True)])
            shape = self.helper.union([shape, self.key_wall_brace(
                x, 0, 0, 1, self.connector.web_post_tl(), x - 1, 0, 0, 1, self.connector.web_post_tr(), back=True
            )])
        shape = self.helper.union([shape, self.key_wall_brace(
            self.settings["lastcol"], 0, 0, 1, self.connector.web_post_tr(), self.settings["lastcol"], 0, 1, 0, self.connector.web_post_tr(), back=True
        )])
        return shape


    def right_wall(self, ):
        logger.debug("right_wall()")

        torow = self.settings["lastrow"] - 1

        if (self.settings["full_last_rows"] or self.settings["ncols"] < 5):
            torow = self.settings["lastrow"]

        tocol = self.settings["lastcol"]

        y = 0
        shape = self.helper.union([
            self.key_wall_brace(
                tocol, y, 1, 0, self.connector.web_post_tr(), tocol, y, 1, 0, self.connector.web_post_br()
            )
        ])

        for i in range(torow):
            y = i + 1
            shape = self.helper.union([shape, self.key_wall_brace(
                tocol, y - 1, 1, 0, self.connector.web_post_br(), tocol, y, 1, 0, self.connector.web_post_tr()
            )])

            shape = self.helper.union([shape, self.key_wall_brace(
                tocol, y, 1, 0, self.connector.web_post_tr(), tocol, y, 1, 0, self.connector.web_post_br()
            )])
            # STRANGE PARTIAL OFFSET

        if self.settings["ncols"] > 4:
            shape = self.helper.union([
                shape,
                self.key_wall_brace(self.settings["lastcol"], torow, 0, -1, self.connector.web_post_br(), self.settings["lastcol"], torow, 1, 0, self.connector.web_post_br())
            ])
        return shape


    def get_left_wall_offsets(self, side="right"):

        wide = 22 if not self.settings["oled_horizontal"] else self.settings["tbiw_left_wall_x_offset_override"]
        short = 8 if not self.settings["oled_horizontal"] else self.settings["tbiw_left_wall_x_offset_override"]
        offsets = [
            short, short, short, short, short, short, short, short
        ]
        if self.settings["trackball_in_wall"] and self.is_side(side, self.settings["ball_side"]):
            wide = self.settings["tbiw_left_wall_x_offset_override"]
            # if oled_mount_type == None or not is_side(side, oled_side):
            #     short = 8
            # else:
            #     left_wall_x_offset = oled_left_wall_x_offset_override
            #     short = tbiw_left_wall_x_offset_override  - 5# HACKISH

            offsets[self.settings["nrows"] - 3] = wide
            offsets[self.settings["nrows"] - 2] = wide
            offsets[self.settings["nrows"] - 1] = wide
            # if nrows == 3:
            #     offsets = [short, wide, wide, wide]
            # elif nrows == 4:
            #     offsets = [short, short, wide, wide]
            # elif nrows == 5:
            #     offsets = [short, short, short, wide, wide]
            # elif nrows == 6:
            #     offsets = [short, short, wide, wide, wide, wide]
        if self.settings["oled_mount_type"] not in [None, "None"] and self.is_side(side, self.settings["oled_side"]):
            left_wall_x_offset = self.settings["oled_left_wall_x_offset_override"]
            wide = self.settings["oled_left_wall_x_offset_override"]
            offsets[0] = wide
            offsets[1] = wide
            offsets[2] = wide
            # if nrows <= 4:
            #     offsets = [wide, wide, wide, wide]
            # elif nrows == 5:
            #     offsets = [wide, wide, wide, short, short]
            # elif nrows == 6:
            #     offsets = [wide, wide, wide, short, short, short]
            # left_wall_x_row_offsets = [22 if row > oled_row else 8 for row in range(lastrow)]

        return offsets


    def left_wall(self, side='right'):
        logger.debug('left_wall()')
        shape = self.helper.union([self.wall_brace(
            (lambda sh: self.capbuilder.key_place( sh, 0, 0)), 0, 1, self.connector.web_post_tl(),
            (lambda sh: self.capbuilder.left_key_place(sh, 0, 1, side=side)), 0, 1, self.connector.web_post(),
        )])

        shape = self.helper.union([shape, self.wall_brace(
            (lambda sh: self.capbuilder.left_key_place(sh, 0, 1, side=side)), 0, 1, self.connector.web_post(),
            (lambda sh: self.capbuilder.left_key_place(sh, 0, 1, side=side)), -1, 0, self.connector.web_post(),
        )])

        for i in range(self.settings["lastrow"]):
            y = i
            low = (y == (self.settings["lastrow"] - 1))
            temp_shape1 = self.wall_brace(
                (lambda sh: self.capbuilder.left_key_place(sh, y, 1, side=side)), -1, 0, self.connector.web_post(),
                (lambda sh: self.capbuilder.left_key_place(sh, y, -1, low_corner=low, side=side)), -1, 0, self.connector.web_post(),
            )
            temp_shape2 = self.helper.hull_from_shapes((
                self.capbuilder.key_place( self.connector.web_post_tl(), 0, y),
                self.capbuilder.key_place( self.connector.web_post_bl(), 0, y),
                self.capbuilder.left_key_place(self.connector.web_post(), y, 1, side=side),
                self.capbuilder.left_key_place(self.connector.web_post(), y, -1, low_corner=low, side=side),
            ))
            shape = self.helper.union([shape, temp_shape1])
            shape = self.helper.union([shape, temp_shape2])

        for i in range(self.settings["lastrow"] - 1):
            y = i + 1
            low = (y == (self.settings["lastrow"] - 1))
            temp_shape1 = self.wall_brace(
                (lambda sh: self.capbuilder.left_key_place(sh, y - 1, -1, side=side)), -1, 0, self.connector.web_post(),
                (lambda sh: self.capbuilder.left_key_place(sh, y, 1, side=side)), -1, 0, self.connector.web_post(),
            )
            temp_shape2 = self.helper.hull_from_shapes((
                self.capbuilder.key_place( self.connector.web_post_tl(), 0, y),
                self.capbuilder.key_place( self.connector.web_post_bl(), 0, y - 1),
                self.capbuilder.left_key_place(self.connector.web_post(), y, 1, side=side),
                self.capbuilder.left_key_place(self.connector.web_post(), y - 1, -1, side=side),
                self.capbuilder.left_key_place(self.connector.web_post(), y - 1, -1, side=side),
            ))
            shape = self.helper.union([shape, temp_shape1])
            shape = self.helper.union([shape, temp_shape2])

        return shape


    def front_wall(self, ):
        logger.debug('front_wall()')

        shape = self.helper.union([
            self.key_wall_brace(
                self.settings["lastcol"], 0, 0, 1, self.connector.web_post_tr(), self.settings["lastcol"], 0, 1, 0, self.connector.web_post_tr()
            )
        ])
        shape = self.helper.union([shape, self.key_wall_brace(
            self.capbuilder.col(3), self.capbuilder.bottom_key(self.capbuilder.col(3)), 0, -1, self.connector.web_post_bl(), self.capbuilder.col(3), self.capbuilder.bottom_key(self.capbuilder.col(3)), 0, -1, self.connector.web_post_br()
        )])
        # shape = union([key_wall_brace(
        #     self.capbuilder.col(3), self.capbuilder.bottom_key(self.capbuilder.col(3)), 0, -1, self.connectors.web_post_bl(), self.capbuilder.col(3), self.capbuilder.bottom_key(self.capbuilder.col(3)), 0.5, -1, self.connector.web_post_br()
        # )])
        shape = self.helper.union([shape, self.key_wall_brace(
            self.capbuilder.col(3), self.capbuilder.bottom_key(self.capbuilder.col(3)), 0, -1, self.connector.web_post_br(), self.capbuilder.col(4), self.capbuilder.bottom_key(self.capbuilder.col(4)), 0.5, -1, self.connector.web_post_bl()
        )])

        min_last_col = self.settings["shift_column"] + 2  # first_self.capbuilder.bottom_key()
        if min_last_col < 0:
            min_last_col = 0
        if min_last_col >= self.settings["ncols"] - 1:
            min_last_col = self.settings["ncols"] - 1

        if self.settings["ncols"] >= min_last_col + 1:
            for i in range(self.settings["ncols"] - (min_last_col + 1)):
                x = i + min_last_col + 1
                shape = self.helper.union([shape, self.key_wall_brace(
                    x, self.capbuilder.bottom_key(x), 0, -1, self.connector.web_post_bl(), x, self.capbuilder.bottom_key(x), 0, -1, self.connector.web_post_br()
                )])

        if self.settings["ncols"] >= min_last_col + 2:
            for i in range(self.settings["ncols"] - (min_last_col + 2)):
                x = i + (min_last_col + 2)
                shape = self.helper.union([shape, self.key_wall_brace(
                    x, self.capbuilder.bottom_key(x), 0, -1, self.connector.web_post_bl(), x - 1, self.capbuilder.bottom_key(x - 1), 0, -1, self.connector.web_post_br()
                )])

        return shape


    def case_walls(self, cluster, side='right'):
        logger.debug('case_walls()')
        return (
            self.helper.union([
                self.back_wall(),
                self.left_wall(side=side),
                self.right_wall(),
                self.front_wall(),
                cluster.walls(side=side),
                cluster.connection(side=side),
            ])
        )

