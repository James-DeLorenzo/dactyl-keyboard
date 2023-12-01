import logging
import numpy as np
from utils.walls import WallBuilder
from utils import plate

logger = logging.getLogger()


class CapBuilder():

    def __init__(self, settings, helper) -> None:
       self.settings = settings
       self.helper = helper

    def col(self, from_column):
        c = from_column + self.settings["shift_column"]  # if not inner_column else from_column - 1
        if c < 0:
            c = 0
        if c > self.settings["ncols"] - 1:
            c = self.settings["ncols"] -1
        return c

    def column_offset(self, column: int) -> list:
        c = column - self.settings["shift_column"]

        if c < 0:
            c = 0
        if c > self.settings["ncols"] - 1:
            c = self.settings["ncols"] - 1

        return self.settings["column_offsets"][c]

    def apply_key_geometry(self, 
            shape,
            translate_fn,
            rotate_x_fn,
            rotate_y_fn,
            column,
            row,
            column_style=None,):
        logger.debug('apply_key_geometry()')

        column_angle = self.settings["beta"] * (self.settings["centercol"] - column)

        column_x_delta_actual = self.settings["column_x_delta"]
        if (self.settings["pinky_1_5U"] and column == self.settings["lastcol"]):
            if row >= self.settings["first_1_5U_row"] and row <= self.settings["last_1_5U_row"]:
                column_x_delta_actual = self.settings["column_x_delta"] - 1.5
                column_angle = self.settings["beta"] * (self.settings["centercol"] - column - 0.27)

        if column_style == "orthographic":
            column_z_delta = self.settings["column_radius"] * (1 - np.cos(column_angle))
            shape = translate_fn(shape, [0, 0, -self.settings["row_radius"]])
            shape = rotate_x_fn(shape, self.settings["alpha"] * (self.settings["centerrow"] - row))
            shape = translate_fn(shape, [0, 0, self.settings["row_radius"]])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(
                shape, [-(column - self.settings["centercol"]) * column_x_delta_actual, 0, column_z_delta]
            )
            shape = translate_fn(shape, self.column_offset(column))

        elif column_style == "fixed":
            shape = rotate_y_fn(shape, self.settings["fixed_angles"][column])
            shape = translate_fn(shape, [self.settings["fixed_x"][column], 0, self.settings["fixed_z"][column]])
            shape = translate_fn(shape, [0, 0, -(self.settings["row_radius"] + self.settings["fixed_z"][column])])
            shape = rotate_x_fn(shape, self.settings["alpha"] * (self.settings["centerrow"] - row), self.helper)
            shape = translate_fn(shape, [0, 0, self.settings["row_radius"] + self.settings["fixed_z"][column]])
            shape = rotate_y_fn(shape, self.settings["fixed_tenting"])
            shape = translate_fn(shape, [0, self.column_offset(column)[1], 0])

        else:
            shape = translate_fn(shape, [0, 0, -self.settings["row_radius"]])
            shape = rotate_x_fn(shape, self.settings["alpha"] * (self.settings["centerrow"] - row))
            shape = translate_fn(shape, [0, 0, self.settings["row_radius"]])
            shape = translate_fn(shape, [0, 0, -self.settings["column_radius"]])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(shape, [0, 0, self.settings["column_radius"]])
            shape = translate_fn(shape, self.column_offset(column))

        shape = rotate_y_fn(shape, self.settings["tenting_angle"])
        shape = translate_fn(shape, [0, 0, self.settings["keyboard_z_offset"]])

        return shape

    def first_bottom_key(self):
        for c in range(self.settings["ncols"] - 1):
            if self.bottom_key(c) == self.settings["nrows"] - 1:
                return c

    def x_rot(self, shape, angle):
        # logger.debug('x_rot()')
        return self.helper.rotate(shape, [np.rad2deg(angle), 0, 0])


    def y_rot(self, shape, angle):
        # logger.debug('y_rot()')
        return self.helper.rotate(shape, [0, np.rad2deg(angle), 0])


    def cluster_key_place(self, shape, column, row):
        logger.debug('key_place()')
        c = self.col(column)
        # if c < 0:
        #     c = 0
        # if c > ncols - 1:
        #     c = ncols - 1
        # c = column if not inner_column else column + 1
        return self.apply_key_geometry(shape, self.helper.translate, self.x_rot, self.y_rot, c, row)

    # This is hackish... It just allows the search and replace of key_place in the cluster code
    # to not go big boom
    def left_cluster_key_place(self, shape, row, direction, low_corner=False, side='right'):
        if row > self.bottom_key(0):
            row = self.bottom_key(0)
        return self.left_key_place(shape, row, direction, low_corner, side)


    def add_translate(self, shape, xyz):
        logger.debug('add_translate()')
        vals = []
        for i in range(len(shape)):
            vals.append(shape[i] + xyz[i])
        return vals

    def rotate_around_x(self, position, angle):
        # logger.debug('rotate_around_x()')
        t_matrix = np.array(
            [
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)


    def rotate_around_y(self, position, angle):
        # logger.debug('rotate_around_y()')
        t_matrix = np.array(
            [
                [np.cos(angle), 0, np.sin(angle)],
                [0, 1, 0],
                [-np.sin(angle), 0, np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)


    def key_position(self, position, column, row):
        logger.debug('key_position()')
        return self.apply_key_geometry( position, self.add_translate, self.rotate_around_x, self.rotate_around_y, column, row)

    def left_key_position(self, row, direction, low_corner=False, side='right'):
        logger.debug("left_key_position()")
        pos = np.array(
            self.key_position([-self.settings["mount_width"] * 0.5, direction * self.settings["mount_height"] * 0.5, 0], 0, row)
        )

        wall_x_offsets = WallBuilder(self.settings, self.helper, self).get_left_wall_offsets(side)

        if self.settings["trackball_in_wall"] and side == self.settings["ball_side"]:

            if low_corner:
                y_offset = self.settings["tbiw_left_wall_lower_y_offset"]
                z_offset = self.settings["tbiw_left_wall_lower_z_offset"]
            else:
                y_offset = 0.0
                z_offset = 0.0

            return list(pos - np.array([
                wall_x_offsets[row],
                -y_offset,
                self.settings["tbiw_left_wall_z_offset_override"] + z_offset
            ]))

        if low_corner:
            y_offset = self.settings["left_wall_lower_y_offset"]
            z_offset = self.settings["left_wall_lower_z_offset"]
        else:
            y_offset = 0.0
            z_offset = 0.0

        return list(pos - np.array([wall_x_offsets[row], -y_offset, self.settings["left_wall_z_offset"] + z_offset]))

    def key_holes(self, side="right"):
        logger.debug('key_holes()')
        # hole = single_plate()
        holes = []
        for column in range(self.settings["ncols"]):
            for row in range(self.settings["nrows"]):
                if self.valid_key(column, row):
                    holes.append(self.key_place(plate.single_plate(self.settings, self.helper, side=side), column, row))

        shape = self.helper.union(holes)

        return shape


    def key_place(self, shape, column, row):
        logger.debug('key_place()')
        return self.apply_key_geometry(shape, self.helper.translate, self.x_rot, self.y_rot, column, row)

    def left_key_place(self, shape, row, direction, low_corner=False, side='right'):
        logger.debug("left_key_place()")
        if row > self.bottom_key(0):
            row = self.bottom_key(0)
        pos = self.left_key_position(row, direction, low_corner=low_corner, side=side)
        return self.helper.translate(shape, pos)

    def bottom_key(self, column):
        # if column < shift_column:  # attempt to make inner columns fewer keys
        #     return nrows - 3
        if self.settings["all_last_rows"]:
            return self.settings["nrows"] - 1
        cluster_columns = 2 + self.settings["shift_column"]
        if column in list(range(cluster_columns)):
            return self.settings["nrows"] - 2
        # if column == 2:
        #     if inner_column:
        #         return nrows - 2
        if self.settings["full_last_rows"] or column < cluster_columns + 2:
            return self.settings["nrows"] - 1

        return self.settings["nrows"] - 2


    def valid_key(self, column, row):
        return row <= self.bottom_key(column)


    def caps(self):
        caps = None
        for column in range(self.settings["ncols"]):
            size = 1
            if self.settings["pinky_1_5U"] and column == self.settings["lastcol"]:
                if row >= self.settings["first_1_5U_row"] and row <= self.settings["last_1_5U_row"]:
                    size = 1.5
            for row in range(self.settings["nrows"]):
                if self.valid_key(column, row):
                    if caps is None:
                        caps = self.key_place(self.sa_cap(size), column, row)
                    else:
                        caps = self.helper.add([caps, self.key_place(self.sa_cap(size), column, row)])

        return caps


    ################
    ## SA Keycaps ##
    ################


    def sa_cap(self, Usize: float =1):
        # MODIFIED TO NOT HAVE THE ROTATION.  NEEDS ROTATION DURING ASSEMBLY
        # sa_length = 18.25

        if Usize == 1:
            bl2 = 18.5 / 2
            bw2 = 18.5 / 2
            m = 17 / 2
            pl2 = 6
            pw2 = 6

        elif Usize == 2:
            bl2 = self.settings["sa_length"]
            bw2 = self.settings["sa_length"] / 2
            m = 0
            pl2 = 16
            pw2 = 6

        elif Usize == 1.5:
            bl2 = self.settings["sa_length"] / 2
            bw2 = 27.94 / 2
            m = 0
            pl2 = 6
            pw2 = 11

        elif Usize == 1.25:  # todo
            bl2 = self.settings["sa_length"] / 2
            bw2 = 22.64 / 2
            m = 0
            pl2 = 16
            pw2 = 11

        else: # same as Usize == 1; removes possibly unbound error
            logger.error ("CAP SIZE NOT STANDARD, size must be set to: 1, 1.25, 1.5, 2")
            exit(88)
        k1 = self.helper.polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
        k1 = self.helper.extrude_poly(outer_poly=k1, height=0.1)
        k1 = self.helper.translate(k1, (0, 0, 0.05))
        k2 = self.helper.polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
        k2 = self.helper.extrude_poly(outer_poly=k2, height=0.1)
        k2 = self.helper.translate(k2, (0, 0, 12.0))
        if m > 0:
            m1 = self.helper.polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
            m1 = self.helper.extrude_poly(outer_poly=m1, height=0.1)
            m1 = self.helper.translate(m1, (0, 0, 6.0))
            key_cap = self.helper.hull_from_shapes((k1, k2, m1))
        else:
            key_cap = self.helper.hull_from_shapes((k1, k2))

        key_cap = self.helper.translate(key_cap, (0, 0, 5 + self.settings["plate_thickness"]))

        if self.settings["show_pcbs"]:
            key_cap = self.helper.add([key_cap, self.key_pcb()])

        return key_cap


    def key_pcb(self):
        shape = self.helper.box(self.settings["pcb_width"], self.settings["pcb_height"], self.settings["pcb_thickness"])
        shape = self.helper.translate(shape, (0, 0, -self.settings["pcb_thickness"] / 2))
        hole = self.helper.cylinder(self.settings["pcb_hole_diameter"] / 2, self.settings["pcb_thickness"] + .2)
        hole = self.helper.translate(hole, (0, 0, -(self.settings["pcb_thickness"] + .1) / 2))
        holes = [
            self.helper.translate(hole, (self.settings["pcb_hole_pattern_width"] / 2, self.settings["pcb_hole_pattern_height"] / 2, 0)),
            self.helper.translate(hole, (-self.settings["pcb_hole_pattern_width"] / 2, self.settings["pcb_hole_pattern_height"] / 2, 0)),
            self.helper.translate(hole, (-self.settings["pcb_hole_pattern_width"] / 2, -self.settings["pcb_hole_pattern_height"] / 2, 0)),
            self.helper.translate(hole, (self.settings["pcb_hole_pattern_width"] / 2, -self.settings["pcb_hole_pattern_height"] / 2, 0)),
        ]
        shape = self.helper.difference(shape, holes)

        return shape

