import argparse
import git
import importlib
import json
import os
import sys
import time
import logging

import numpy as np
from numpy import pi
from os import path
import os.path as path

from clusters.default_cluster import DefaultCluster
from clusters.carbonfet import CarbonfetCluster
from clusters.mini import MiniCluster
from clusters.minidox import MinidoxCluster
from clusters.minithicc import Minithicc
from clusters.minithicc3 import Minithicc3
from clusters.trackball_orbyl import TrackballOrbyl
from clusters.trackball_wilder import TrackballWild
from clusters.trackball_three import TrackballThree
from clusters.trackball_cj import TrackballCJ
from clusters.custom_cluster import CustomCluster
from clusters.trackball_btu import TrackballBTU
from json_loader import load_json



def get_git_info():
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    active_branch = repo.active_branch.name
    return {
        "branch": active_branch,
        "sha": sha,
        "datetime": time.ctime(time.time()),
        "dirty": repo.is_dirty()
    }
    # try:
    #     output = str(
    #         subprocess.check_output(
    #             ['git', 'branch'], cwd=path.abspath('.'), universal_newlines=True
    #         )
    #     )
    #     branch = [a for a in output.split('\n') if a.find('*') >= 0][0]
    #     return branch[branch.find('*') + 2:]
    # except subprocess.CalledProcessError:
    #     return None
    # except FileNotFoundError:
    #     log("No git repository found.", "ERROR")
    #     return None
debug_exports = False
debug_trace = False

logging.basicConfig(level=os.environ.get("LOG_LEVEL",logging.INFO))
logger = logging.getLogger()


###############################################
# EXTREMELY UGLY BUT FUNCTIONAL BOOTSTRAP
###############################################

## IMPORT DEFAULT CONFIG IN CASE NEW PARAMETERS EXIST

def make_dactyl(args):
    def is_side(side, param):
        return param == side or param == "both"

    def is_oled(side):
        return settings["oled_mount_type"] not in [None, "None"] and is_side(side, settings["oled_side"])

    def get_left_wall_offsets(side="right"):

        wide = 22 if not settings["oled_horizontal"] else settings["tbiw_left_wall_x_offset_override"]
        short = 8 if not settings["oled_horizontal"] else settings["tbiw_left_wall_x_offset_override"]
        offsets = [
            short, short, short, short, short, short, short, short
        ]
        if settings["trackball_in_wall"] and is_side(side, settings["ball_side"]):
            wide = settings["tbiw_left_wall_x_offset_override"]
            # if oled_mount_type == None or not is_side(side, oled_side):
            #     short = 8
            # else:
            #     left_wall_x_offset = oled_left_wall_x_offset_override
            #     short = tbiw_left_wall_x_offset_override  - 5# HACKISH

            offsets[settings["nrows"] - 3] = wide
            offsets[settings["nrows"] - 2] = wide
            offsets[settings["nrows"] - 1] = wide
            # if nrows == 3:
            #     offsets = [short, wide, wide, wide]
            # elif nrows == 4:
            #     offsets = [short, short, wide, wide]
            # elif nrows == 5:
            #     offsets = [short, short, short, wide, wide]
            # elif nrows == 6:
            #     offsets = [short, short, wide, wide, wide, wide]
        if settings["oled_mount_type"] not in [None, "None"] and is_side(side, settings["oled_side"]):
            left_wall_x_offset = settings["oled_left_wall_x_offset_override"]
            wide = settings["oled_left_wall_x_offset_override"]
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

    right_cluster = None
    left_cluster = None

    left_wall_x_offset = 8
    # left_wall_x_row_offsets = [
    #     8, 8, 8, 8, 8, 8, 8, 8
    # ]
    left_wall_z_offset = 3
    left_wall_lower_y_offset = 0
    left_wall_lower_z_offset = 0

    symmetry = None
    column_style = None
    save_path = path.join(r".", "things")

    matrix = {
        "right": [],
        "left": []
    }

    def cluster(side="right"):
        return right_cluster if side == "right" else left_cluster

    settings = {}

    import generate_configuration as cfg
    settings = cfg.shape_config

    data = None

    overrides_name = ""

    git_data = get_git_info()
    local_branch = git_data["branch"]
        ## CHECK FOR CONFIG FILE AND WRITE TO ANY VARIABLES IN FILE.
    if args.config:
        with open(os.path.join(r".", "configs", args.config + '.json'), mode='r') as fid:
            data = json.load(fid)
    if args.output:
        logger.info(f"save_path set to argument: {args.output}")
        save_path = args.output
    if args.overrides:
        logger.info(f"overrides set to: {args.overrides}")
        overrides_name = args.overrides

    if data is None:
        logger.info(f">>> Using config run_config.json on Git branch {local_branch}")
        data = load_json(os.path.join("src", "run_config.json"), None, save_path)
        # with open(os.path.join("src", "run_config.json"), mode='r') as fid:
        #     data = json.load(fid)

    if data["overrides"] not in [None, ""]:
        if overrides_name != "":
            logger.error("YO! overrides param set in run_config.json AND in command line 'overrides' argument! Can't compute!")
            sys.exit(99)
        overrides_name = data["overrides"]

        # for item in override_data:
        #     data[item] = override_data[item]
    if overrides_name != "":
        logger.info(f"Importing config overrides for: {overrides_name}")
        save_path = path.join(save_path, overrides_name)
        override_file = path.join(save_path, overrides_name + '.json')
        with open(override_file, mode='r') as fid:
            data = load_json(override_file, data, save_path)

    try:
        if data["branch"] not in ["", None]:
            if data["branch"] != local_branch:
                logger.error(f"INCORRECT GIT BRANCH! Local is {local_branch} but config requires {data['branch']}.  Exiting.")
                sys.exit(101)
    except Exception:
        logger.warn("No 'branch' param found on config.")

    settings.update(data)

    if settings["save_name"] not in ['', None]:
        config_name = settings["save_name"]
        r_config_name = settings["save_name"]
        l_config_name = settings["save_name"]
    elif overrides_name is not None:
        config_name = overrides_name + "_" + str(settings["nrows"]) + "x" + str(settings["ncols"])
        r_config_name = config_name + "_" + settings["thumb_style"]
        l_config_name = config_name + "_" + settings["other_thumb"]

    ENGINE = data["ENGINE"]
    # Really rough setup.  Check for ENGINE, set it not present from configuration.
    try:
        logger.info(f'Found Current Engine in Config = {ENGINE}')
    except Exception:
        logger.warn('Engine Not Found in Config')
        ENGINE = 'solid'
        # ENGINE = 'cadquery'
        logger.info(f'Setting Current Engine = {ENGINE}')

    parts_path = os.path.abspath(path.join(r"src", "parts"))

    if settings["save_dir"] not in ['', None, '.']:
        save_path = settings["save_dir"]
        logger.info(f"save_path set to save_dir json setting: {save_path}")
            # parts_path = path.join(r"..", r"..", "src", "parts")
        # parts_path = path.join(r"..", r"..", "src", "parts")

        # parts_path = path.jo

    dir_exists = os.path.isdir(save_path)
    if not dir_exists:
        os.makedirs(save_path, exist_ok=True)

    ###############################################
    # END EXTREMELY UGLY BOOTSTRAP
    ###############################################

    ####################################################
    # HELPER FUNCTIONS TO MERGE CADQUERY AND OPENSCAD
    ####################################################

    if ENGINE == 'cadquery':
        import helpers_cadquery as helpers
    else:
        import helpers_solid as helpers

    ####################################################
    # END HELPER FUNCTIONS
    ####################################################

    quickly = False
    global quick_render
    try:
        if quick_render:
            quickly = quick_render
    except NameError:
        quickly = False

    if settings["oled_mount_type"] is not None and settings["oled_mount_type"] != "NONE":
        for item in settings["oled_configurations"][settings["oled_mount_type"]]:
            globals()[item] = settings["oled_configurations"][settings["oled_mount_type"]][item]

    if settings["nrows"] > 5:
        column_style = settings["column_style_gt5"]

    centerrow = settings["nrows"] - settings["centerrow_offset"]

    lastrow = settings["nrows"] - 1
    cornerrow = lastrow - 1
    lastcol = settings["ncols"] - 1

    oled_row = settings["nrows"] - 1
    plate_file = None

    # Derived values
    if settings["plate_style"] in ['NUB', 'HS_NUB']:
        keyswitch_height = settings["nub_keyswitch_height"]
        keyswitch_width = settings["nub_keyswitch_width"]
    elif settings["plate_style"] in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
        keyswitch_height = settings["undercut_keyswitch_height"]
        keyswitch_width = settings["undercut_keyswitch_width"]
    else:
        keyswitch_height = settings["hole_keyswitch_height"]
        keyswitch_width = settings["hole_keyswitch_width"]

    if "AMOEBA" in settings["plate_style"]:
        symmetry = "asymmetric"
        plate_file = path.join(parts_path, r"amoeba_key_hole")
    elif 'HS_' in settings["plate_style"]:
        symmetry = "asymmetric"
        pname = r"hot_swap_plate"
        if settings["plate_file_name"] is not None:
            pname = settings["plate_file_name"]
        plate_file = path.join(parts_path, pname)
        # plate_offset = 0.0 # this overwrote the config variable

    if (settings["trackball_in_wall"] or ('TRACKBALL' in settings["thumb_style"])) and not settings["ball_side"] == 'both':
        symmetry = "asymmetric"

    mount_width = keyswitch_width + 2 * settings["plate_rim"]
    mount_height = keyswitch_height + 2 * settings["plate_rim"]
    mount_thickness = settings["plate_thickness"]

    if settings["default_1U_cluster"] and settings["thumb_style"] == 'DEFAULT':
        double_plate_height = (.7 * settings["sa_double_length"] - mount_height) / 3
        # double_plate_height = (.95 * sa_double_length - mount_height) / 3
    elif settings["thumb_style"] == 'DEFAULT':
        double_plate_height = (.90 * settings["sa_double_length"] - mount_height) / 3
    else:
        double_plate_height = (settings["sa_double_length"] - mount_height) / 3

    # wide = 22 if not oled_horizontal else tbiw_left_wall_x_offset_override
    # short = 8 if not oled_horizontal else tbiw_left_wall_x_offset_override
    #
    # if oled_mount_type is not None and oled_mount_type != "NONE":
    #     left_wall_x_offset = oled_left_wall_x_offset_override
    #     if nrows <= 4:
    #         left_wall_x_row_offsets = [wide, wide, wide, wide]
    #     elif nrows == 5:
    #         left_wall_x_row_offsets = [wide, wide, wide, short, short]
    #     elif nrows == 6:
    #         left_wall_x_row_offsets = [wide, wide, wide, short, short, short]
    #     # left_wall_x_row_offsets = [22 if row > oled_row else 8 for row in range(lastrow)]
    #     left_wall_z_offset = oled_left_wall_z_offset_override
    #     left_wall_lower_y_offset = oled_left_wall_lower_y_offset
    #     left_wall_lower_z_offset = oled_left_wall_lower_z_offset

    cap_top_height = settings["plate_thickness"] + settings["sa_profile_key_height"]
    row_radius = ((mount_height + settings["extra_height"]) / 2) / (np.sin(settings["alpha"] / 2)) + cap_top_height
    column_radius = (
                            ((mount_width + settings["extra_width"]) / 2) / (np.sin(settings["beta"] / 2))
                    ) + cap_top_height
    column_x_delta = -1 - column_radius * np.sin(settings["beta"])
    column_base_angle = settings["beta"] * (settings["centercol"] - 2)

    teensy_width = 20
    teensy_height = 12
    teensy_length = 33
    teensy2_length = 53
    teensy_pcb_thickness = 2
    teensy_offset_height = 5
    teensy_holder_top_length = 18
    teensy_holder_width = 7 + teensy_pcb_thickness
    teensy_holder_height = 6 + teensy_width

    # todo
    def build_matrix():
        return matrix

    def build_layout():
        return matrix

    # save_path = path.join("..", "things", save_dir)
    if not path.isdir(save_path):
        os.mkdir(save_path)

    if settings["layouts"] is not None:
        matrix = build_layout()
    else:
        left_matrix = build_matrix()

    def col(from_column):
        c = from_column + settings["shift_column"]  # if not inner_column else from_column - 1
        if c < 0:
            c = 0
        if c > settings["ncols"] - 1:
            c = settings["ncols"] -1
        return c

    def column_offset(column: int) -> list:
        c = column - settings["shift_column"]

        if c < 0:
            c = 0
        if c > settings["ncols"] - 1:
            c = settings["ncols"] - 1

        return settings["column_offsets"][c]


    def single_plate(cylinder_segments=100, side="right"):
        if settings["plate_style"] == "MXLEDBIT":
            pcb_width = 19
            pcb_length = 19
            pcb_height = 1.6

            # degrees = np.degrees(alpha / 2)
            # frame = box(pcb_width + 2, pcb_length + 2, pcb_height * 2)
            # cutout = union([box(pcb_width - 1, pcb_length - 1, pcb_height * 4),
            #                 translate(box(pcb_width + 0.2, pcb_height + 0.2, pcb_height * 2), (0, 0, -(pcb_height / 2)))])
            # # # frame = difference(frame, [box(pcb_width - 1, pcb_length - 1, pcb_height * 4)])
            # frame = difference(frame, [cutout])
            # connector = translate(rotate(box(pcb_width + 2, extra_height * 2, pcb_height * 2), (degrees, 0, 0)), (0, (pcb_length / 2), 0))
            # frame = union([frame, connector])

            degrees = np.degrees(settings["alpha"] / 2)
            frame = helpers.box(21, 21, 3)
            # # frame = difference(frame, [box(pcb_width - 1, pcb_length - 1, pcb_height * 4)])
            frame = helpers.difference(frame, [helpers.box(18.5, 18.5, 5)])
            frame = helpers.difference(frame, [helpers.box(19.5, 19.5, 2.5)])
            connector = helpers.translate(helpers.rotate(helpers.box(21, 4, 2.5), (degrees, 0, 0)), (0, 11.5, 0))
            frame = helpers.translate(helpers.union([frame, connector]), (0, 0, -5))
            return frame

        if settings["plate_style"] in ['NUB', 'HS_NUB']:
            tb_border = (mount_height - keyswitch_height) / 2
            top_wall = helpers.box(mount_width, tb_border, settings["plate_thickness"])
            top_wall = helpers.translate(top_wall, (0, (tb_border / 2) + (keyswitch_height / 2), settings["plate_thickness"] / 2))

            lr_border = (mount_width - keyswitch_width) / 2
            left_wall = helpers.box(lr_border, mount_height, settings["plate_thickness"])
            left_wall = helpers.translate(left_wall, ((lr_border / 2) + (keyswitch_width / 2), 0, settings["plate_thickness"] / 2))

            side_nub = helpers.cylinder(radius=1, height=2.75)
            side_nub = helpers.rotate(side_nub, (90, 0, 0))
            side_nub = helpers.translate(side_nub, (keyswitch_width / 2, 0, 1))

            nub_cube = helpers.box(1.5, 2.75, settings["plate_thickness"])
            nub_cube = helpers.translate(nub_cube, ((1.5 / 2) + (keyswitch_width / 2), 0, settings["plate_thickness"] / 2))

            side_nub2 = helpers.tess_hull(shapes=(side_nub, nub_cube))
            side_nub2 = helpers.union([side_nub2, side_nub, nub_cube])

            plate_half1 = helpers.union([top_wall, left_wall, side_nub2])
            plate_half2 = plate_half1
            plate_half2 = helpers.mirror(plate_half2, 'XZ')
            plate_half2 = helpers.mirror(plate_half2, 'YZ')

            plate = helpers.union([plate_half1, plate_half2])

        # elif plate_style in "AMOEBA":  # 'HOLE' or default, square cutout for non-nub designs.
        #     plate = box(mount_width, mount_height, mount_thickness)
        #     plate = translate(plate, (0.0, 0.0, mount_thickness / 2.0))
        #
        #     shape_cut = box(keyswitch_width + 2, keyswitch_height + 2, mount_thickness * 2 + .02)
        #     shape_cut = translate(shape_cut, (0.0, 0.0, mount_thickness - .01))
        #
        #     plate = difference(plate, [shape_cut])

        else:  # 'HOLE' or default, square cutout for non-nub designs.
            plate = helpers.box(mount_width, mount_height, mount_thickness)
            plate = helpers.translate(plate, (0.0, 0.0, mount_thickness / 2.0))

            shape_cut = helpers.box(keyswitch_width, keyswitch_height, mount_thickness * 2 + .02)
            shape_cut = helpers.translate(shape_cut, (0.0, 0.0, mount_thickness - .01))

            plate = helpers.difference(plate, [shape_cut])

        if plate_file is not None:
            socket = helpers.import_file(plate_file)
            socket = helpers.translate(socket, [0, 0, settings["plate_thickness"] + settings["plate_offset"]])
            plate = helpers.union([plate, socket])

        if settings["plate_style"] in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH', 'AMOEBA']:
            if settings["plate_style"] in ['UNDERCUT', 'HS_UNDERCUT']:
                undercut = helpers.box(
                    keyswitch_width + 2 * settings["clip_undercut"],
                    keyswitch_height + 2 * settings["clip_undercut"],
                    mount_thickness
                )

            if settings["plate_style"] in ['NOTCH', 'HS_NOTCH', 'AMOEBA']:
                undercut = helpers.box(
                    settings["notch_width"],
                    keyswitch_height + 2 * settings["clip_undercut"],
                    mount_thickness
                )
                undercut = helpers.union([undercut,
                    helpers.box(
                        keyswitch_width + 2 * settings["clip_undercut"],
                        settings["notch_width"],
                        mount_thickness
                    )
                ])

            undercut = helpers.translate(settings["undercut"], (0.0, 0.0, -settings["clip_thickness"] + mount_thickness / 2.0))

            if ENGINE == 'cadquery' and settings["undercut_transition"] > 0:
                undercut = undercut.faces("+Z").chamfer(settings["undercut_transition"], settings["clip_undercut"])

            plate = helpers.difference(plate, [undercut])

        # if plate_file is not None:
        #     socket = import_file(plate_file)
        #
        #     socket = translate(socket, [0, 0, plate_thickness + plate_offset])
        #     plate = union([plate, socket])

        if settings["plate_holes"]:
            half_width = settings["plate_holes_width"] / 2.
            half_height = settings["plate_holes_height"] / 2.
            x_off = settings["plate_holes_xy_offset"][0]
            y_off = settings["plate_holes_xy_offset"][1]
            holes = [
                helpers.translate(
                    helpers.cylinder(radius=settings["plate_holes_diameter"] / 2, height=settings["plate_holes_depth"] + .01),
                    (x_off + half_width, y_off + half_height, settings["plate_holes_depth"] / 2 - .01)
                ),
                helpers.translate(
                    helpers.cylinder(radius=settings["plate_holes_diameter"] / 2, height=settings["plate_holes_depth"] + .01),
                    (x_off - half_width, y_off + half_height, settings["plate_holes_depth"] / 2 - .01)
                ),
                helpers.translate(
                    helpers.cylinder(radius=settings["plate_holes_diameter"] / 2, height=settings["plate_holes_depth"] + .01),
                    (x_off - half_width, y_off - half_height, settings["plate_holes_depth"] / 2 - .01)
                ),
                helpers.translate(
                    helpers.cylinder(radius=settings["plate_holes_diameter"] / 2, height=settings["plate_holes_depth"] + .01),
                    (x_off + half_width, y_off - half_height, settings["plate_holes_depth"] / 2 - .01)
                ),
            ]
            plate = helpers.difference(plate, holes)

        if side == "left":
            plate = helpers.mirror(plate, 'YZ')

        return plate


    ################
    ## SA Keycaps ##
    ################


    def sa_cap(Usize: float =1):
        # MODIFIED TO NOT HAVE THE ROTATION.  NEEDS ROTATION DURING ASSEMBLY
        # sa_length = 18.25

        if Usize == 1:
            bl2 = 18.5 / 2
            bw2 = 18.5 / 2
            m = 17 / 2
            pl2 = 6
            pw2 = 6

        elif Usize == 2:
            bl2 = settings["sa_length"]
            bw2 = settings["sa_length"] / 2
            m = 0
            pl2 = 16
            pw2 = 6

        elif Usize == 1.5:
            bl2 = settings["sa_length"] / 2
            bw2 = 27.94 / 2
            m = 0
            pl2 = 6
            pw2 = 11

        elif Usize == 1.25:  # todo
            bl2 = settings["sa_length"] / 2
            bw2 = 22.64 / 2
            m = 0
            pl2 = 16
            pw2 = 11

        else: # same as Usize == 1; removes possibly unbound error
            logger.error ("CAP SIZE NOT STANDARD, size must be set to: 1, 1.25, 1.5, 2")
            exit(88)
        k1 = helpers.polyline([(bw2, bl2), (bw2, -bl2), (-bw2, -bl2), (-bw2, bl2), (bw2, bl2)])
        k1 = helpers.extrude_poly(outer_poly=k1, height=0.1)
        k1 = helpers.translate(k1, (0, 0, 0.05))
        k2 = helpers.polyline([(pw2, pl2), (pw2, -pl2), (-pw2, -pl2), (-pw2, pl2), (pw2, pl2)])
        k2 = helpers.extrude_poly(outer_poly=k2, height=0.1)
        k2 = helpers.translate(k2, (0, 0, 12.0))
        if m > 0:
            m1 = helpers.polyline([(m, m), (m, -m), (-m, -m), (-m, m), (m, m)])
            m1 = helpers.extrude_poly(outer_poly=m1, height=0.1)
            m1 = helpers.translate(m1, (0, 0, 6.0))
            key_cap = helpers.hull_from_shapes((k1, k2, m1))
        else:
            key_cap = helpers.hull_from_shapes((k1, k2))

        key_cap = helpers.translate(key_cap, (0, 0, 5 + settings["plate_thickness"]))

        if settings["show_pcbs"]:
            key_cap = helpers.add([key_cap, key_pcb()])

        return key_cap


    def key_pcb():
        shape = helpers.box(settings["pcb_width"], settings["pcb_height"], settings["pcb_thickness"])
        shape = helpers.translate(shape, (0, 0, -settings["pcb_thickness"] / 2))
        hole = helpers.cylinder(settings["pcb_hole_diameter"] / 2, settings["pcb_thickness"] + .2)
        hole = helpers.translate(hole, (0, 0, -(settings["pcb_thickness"] + .1) / 2))
        holes = [
            helpers.translate(hole, (settings["pcb_hole_pattern_width"] / 2, settings["pcb_hole_pattern_height"] / 2, 0)),
            helpers.translate(hole, (-settings["pcb_hole_pattern_width"] / 2, settings["pcb_hole_pattern_height"] / 2, 0)),
            helpers.translate(hole, (-settings["pcb_hole_pattern_width"] / 2, -settings["pcb_hole_pattern_height"] / 2, 0)),
            helpers.translate(hole, (settings["pcb_hole_pattern_width"] / 2, -settings["pcb_hole_pattern_height"] / 2, 0)),
        ]
        shape = helpers.difference(shape, holes)

        return shape


    #########################
    ## Placement Functions ##
    #########################


    def rotate_around_x(position, angle):
        # logger.debug('rotate_around_x()')
        t_matrix = np.array(
            [
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)


    def rotate_around_y(position, angle):
        # logger.debug('rotate_around_y()')
        t_matrix = np.array(
            [
                [np.cos(angle), 0, np.sin(angle)],
                [0, 1, 0],
                [-np.sin(angle), 0, np.cos(angle)],
            ]
        )
        return np.matmul(t_matrix, position)


    def apply_key_geometry(
            shape,
            translate_fn,
            rotate_x_fn,
            rotate_y_fn,
            column,
            row,
            column_style=column_style,
    ):
        logger.debug('apply_key_geometry()')

        column_angle = settings["beta"] * (settings["centercol"] - column)

        column_x_delta_actual = column_x_delta
        if (settings["pinky_1_5U"] and column == lastcol):
            if row >= settings["first_1_5U_row"] and row <= settings["last_1_5U_row"]:
                column_x_delta_actual = column_x_delta - 1.5
                column_angle = settings["beta"] * (settings["centercol"] - column - 0.27)

        if column_style == "orthographic":
            column_z_delta = column_radius * (1 - np.cos(column_angle))
            shape = translate_fn(shape, [0, 0, -row_radius])
            shape = rotate_x_fn(shape, settings["alpha"] * (centerrow - row))
            shape = translate_fn(shape, [0, 0, row_radius])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(
                shape, [-(column - settings["centercol"]) * column_x_delta_actual, 0, column_z_delta]
            )
            shape = translate_fn(shape, column_offset(column))

        elif column_style == "fixed":
            shape = rotate_y_fn(shape, settings["fixed_angles"][column])
            shape = translate_fn(shape, [settings["fixed_x"][column], 0, settings["fixed_z"][column]])
            shape = translate_fn(shape, [0, 0, -(row_radius + settings["fixed_z"][column])])
            shape = rotate_x_fn(shape, settings["alpha"] * (centerrow - row))
            shape = translate_fn(shape, [0, 0, row_radius + settings["fixed_z"][column]])
            shape = rotate_y_fn(shape, settings["fixed_tenting"])
            shape = translate_fn(shape, [0, column_offset(column)[1], 0])

        else:
            shape = translate_fn(shape, [0, 0, -row_radius])
            shape = rotate_x_fn(shape, settings["alpha"] * (centerrow - row))
            shape = translate_fn(shape, [0, 0, row_radius])
            shape = translate_fn(shape, [0, 0, -column_radius])
            shape = rotate_y_fn(shape, column_angle)
            shape = translate_fn(shape, [0, 0, column_radius])
            shape = translate_fn(shape, column_offset(column))

        shape = rotate_y_fn(shape, settings["tenting_angle"])
        shape = translate_fn(shape, [0, 0, settings["keyboard_z_offset"]])

        return shape

    def bottom_key(column):
        # if column < shift_column:  # attempt to make inner columns fewer keys
        #     return nrows - 3
        if settings["all_last_rows"]:
            return settings["nrows"] - 1
        cluster_columns = 2 + settings["shift_column"]
        if column in list(range(cluster_columns)):
            return settings["nrows"] - 2
        # if column == 2:
        #     if inner_column:
        #         return nrows - 2
        if settings["full_last_rows"] or column < cluster_columns + 2:
            return settings["nrows"] - 1

        return settings["nrows"] - 2


    def first_bottom_key():
        for c in range(settings["ncols"] - 1):
            if bottom_key(c) == settings["nrows"] - 1:
                return c


    def valid_key(column, row):
        return row <= bottom_key(column)

    def x_rot(shape, angle):
        # logger.debug('x_rot()')
        return helpers.rotate(shape, [np.rad2deg(angle), 0, 0])


    def y_rot(shape, angle):
        # logger.debug('y_rot()')
        return helpers.rotate(shape, [0, np.rad2deg(angle), 0])


    def key_place(shape, column, row):
        logger.debug('key_place()')
        return apply_key_geometry(shape, helpers.translate, x_rot, y_rot, column, row)


    def cluster_key_place(shape, column, row):
        logger.debug('key_place()')
        c = col(column)
        # if c < 0:
        #     c = 0
        # if c > ncols - 1:
        #     c = ncols - 1
        # c = column if not inner_column else column + 1
        return apply_key_geometry(shape, settings["translate"], x_rot, y_rot, c, row)
    def add_translate(shape, xyz):
        logger.debug('add_translate()')
        vals = []
        for i in range(len(shape)):
            vals.append(shape[i] + xyz[i])
        return vals


    def key_position(position, column, row):
        logger.debug('key_position()')
        return apply_key_geometry(
            position, add_translate, rotate_around_x, rotate_around_y, column, row
        )


    def key_holes(side="right"):
        logger.debug('key_holes()')
        # hole = single_plate()
        holes = []
        for column in range(settings["ncols"]):
            for row in range(settings["nrows"]):
                if valid_key(column, row):
                    holes.append(key_place(single_plate(side=side), column, row))

        shape = helpers.union(holes)

        return shape


    def caps():
        caps = None
        for column in range(settings["ncols"]):
            size = 1
            if settings["pinky_1_5U"] and column == lastcol:
                if row >= settings["first_1_5U_row"] and row <= settings["last_1_5U_row"]:
                    size = 1.5
            for row in range(settings["nrows"]):
                if valid_key(column, row):
                    if caps is None:
                        caps = key_place(sa_cap(size), column, row)
                    else:
                        caps = helpers.add([caps, key_place(sa_cap(size), column, row)])

        return caps


    ####################
    ## Web Connectors ##
    ####################


    def web_post():
        logger.debug('web_post()')
        post = helpers.box(settings["post_size"], settings["post_size"], settings["web_thickness"])
        post = helpers.translate(post, (0, 0, settings["plate_thickness"] - (settings["web_thickness"] / 2)))
        return post


    def web_post_tr(off_w=0, off_h=0, off_z=0):
        return helpers.translate(web_post(), ((mount_width / 2.0) + off_w, (mount_height / 2.0) + off_h, 0))


    def web_post_tl(off_w=0, off_h=0, off_z=0):
        return helpers.translate(web_post(), (-(mount_width / 2.0) - off_w, (mount_height / 2.0) + off_h, 0))


    def web_post_bl(off_w=0, off_h=0, off_z=0):
        return helpers.translate(web_post(), (-(mount_width / 2.0) - off_w, -(mount_height / 2.0) - off_h, 0))


    def web_post_br(off_w=0, off_h=0, off_z=0):
        return helpers.translate(web_post(), ((mount_width / 2.0) + off_w, -(mount_height / 2.0) - off_h, 0))

    def get_torow(column):
        return bottom_key(column) + 1
        # torow = lastrow
        # if full_last_rows or (column == 4 and inner_column):
        #     torow = lastrow + 1
        #
        # if column in [0, 1]:
        #     torow = lastrow
        # return torow


    def connectors():
        logger.debug('connectors()')
        hulls = []
        for column in range(settings["ncols"] - 1):
            torow = get_torow(column)
            if not settings["full_last_rows"] and column == 3:
                torow -= 1

            for row in range(torow):  # need to consider last_row?
                # for row in range(nrows):  # need to consider last_row?
                places = []
                next_row = row if row <= bottom_key(column + 1) else bottom_key(column + 1)
                places.append(key_place(web_post_tl(), column + 1, next_row))
                places.append(key_place(web_post_tr(), column, row))
                places.append(key_place(web_post_bl(), column + 1, next_row))
                places.append(key_place(web_post_br(), column, row))
                hulls.append(helpers.triangle_hulls(places))

        for column in range(settings["ncols"]):
            torow = get_torow(column)
            # for row in range(nrows-1):
            # next_row = row + 1 if row + 1 < bottom_key(column) else bottom_key(column)
            for row in range(torow - 1):
                places = []
                places.append(key_place(web_post_bl(), column, row))
                places.append(key_place(web_post_br(), column, row))
                places.append(key_place(web_post_tl(), column, row + 1))
                places.append(key_place(web_post_tr(), column, row + 1))
                hulls.append(helpers.triangle_hulls(places))

        for column in range(settings["ncols"] - 1):
            torow = get_torow(column)
            # for row in range(nrows-1):  # need to consider last_row?
            for row in range(torow - 1):  # need to consider last_row?
                next_row = row if row < bottom_key(column + 1) else bottom_key(column + 1) - 1

                places = []
                places.append(key_place(web_post_br(), column, row))
                places.append(key_place(web_post_tr(), column, row + 1))
                places.append(key_place(web_post_bl(), column + 1, next_row))
                places.append(key_place(web_post_tl(), column + 1, next_row + 1))
                hulls.append(helpers.triangle_hulls(places))

        return helpers.union(hulls)


    ############
    ## Thumbs ##
    ############


    def adjustable_plate_size(Usize=1.5):
        return (Usize * settings["sa_length"] - mount_height) / 2


    def adjustable_plate_half(Usize=1.5):
        logger.debug('double_plate()')
        adjustable_plate_height = adjustable_plate_size(Usize)
        top_plate = helpers.box(mount_width, adjustable_plate_height, settings["web_thickness"])
        top_plate = helpers.translate(top_plate,
                              [0, (adjustable_plate_height + mount_height) / 2, settings["plate_thickness"] - (settings["web_thickness"] / 2)]
                              )
        return top_plate


    def adjustable_plate(Usize=1.5):
        logger.debug('double_plate()')
        top_plate = adjustable_plate_half(Usize)
        return helpers.union((top_plate, helpers.mirror(top_plate, 'XZ')))


    def double_plate_half():
        logger.debug('double_plate()')
        top_plate = helpers.box(mount_width, double_plate_height, settings["web_thickness"])
        top_plate = helpers.translate(top_plate,
                              [0, (double_plate_height + mount_height) / 2, settings["plate_thickness"] - (settings["web_thickness"] / 2)]
                              )
        return top_plate


    def double_plate():
        logger.debug('double_plate()')
        top_plate = double_plate_half()
        return helpers.union((top_plate, helpers.mirror(top_plate, 'XZ')))


    ############################
    # MINI THUMB CLUSTER
    ############################


    ############################
    # MINIDOX (3-key) THUMB CLUSTER
    ############################


    ############################
    # Carbonfet THUMB CLUSTER
    ############################


    ############################
    # Wilder Trackball (Ball + 4-key) THUMB CLUSTER
    ############################


    ############################
    # CJ TRACKBALL THUMB CLUSTER
    ############################

    # single_plate = the switch shape


    ##########
    ## Case ##
    ##########

    def left_key_position(row, direction, low_corner=False, side='right'):
        logger.debug("left_key_position()")
        pos = np.array(
            key_position([-mount_width * 0.5, direction * mount_height * 0.5, 0], 0, row)
        )

        wall_x_offsets = get_left_wall_offsets(side)

        if settings["trackball_in_wall"] and is_side(side, settings["ball_side"]):

            if low_corner:
                y_offset = settings["tbiw_left_wall_lower_y_offset"]
                z_offset = settings["tbiw_left_wall_lower_z_offset"]
            else:
                y_offset = 0.0
                z_offset = 0.0

            return list(pos - np.array([
                wall_x_offsets[row],
                -y_offset,
                settings["tbiw_left_wall_z_offset_override"] + z_offset
            ]))

        if low_corner:
            y_offset = left_wall_lower_y_offset
            z_offset = left_wall_lower_z_offset
        else:
            y_offset = 0.0
            z_offset = 0.0

        return list(pos - np.array([wall_x_offsets[row], -y_offset, left_wall_z_offset + z_offset]))


    def left_key_place(shape, row, direction, low_corner=False, side='right'):
        logger.debug("left_key_place()")
        if row > bottom_key(0):
            row = bottom_key(0)
        pos = left_key_position(row, direction, low_corner=low_corner, side=side)
        return helpers.translate(shape, pos)

    # This is hackish... It just allows the search and replace of key_place in the cluster code
    # to not go big boom
    def left_cluster_key_place(shape, row, direction, low_corner=False, side='right'):
        if row > bottom_key(0):
            row = bottom_key(0)
        return left_key_place(shape, row, direction, low_corner, side)

    def wall_locate1(dx, dy):
        logger.debug("wall_locate1()")
        return [dx * settings["wall_thickness"], dy * settings["wall_thickness"], -1]


    def wall_locate2(dx, dy):
        logger.debug("wall_locate2()")
        return [dx * settings["wall_x_offset"], dy * settings["wall_y_offset"], -settings["wall_z_offset"]]


    def wall_locate3(dx, dy, back=False):
        logger.debug("wall_locate3()")
        if back:
            return [
                dx * (settings["wall_x_offset"] + settings["wall_base_x_thickness"]),
                dy * (settings["wall_y_offset"] + settings["wall_base_back_thickness"]),
                -settings["wall_z_offset"],
            ]
        else:
            return [
                dx * (settings["wall_x_offset"] + settings["wall_base_x_thickness"]),
                dy * (settings["wall_y_offset"] + settings["wall_base_y_thickness"]),
                -settings["wall_z_offset"],
            ]
        # return [
        #     dx * (wall_xy_offset + wall_thickness),
        #     dy * (wall_xy_offset + wall_thickness),
        #     -wall_z_offset,
        # ]


    def wall_brace(place1, dx1, dy1, post1, place2, dx2, dy2, post2, back=False):
        logger.debug("wall_brace()")
        hulls = []

        hulls.append(place1(post1))
        hulls.append(place1(helpers.translate(post1, wall_locate1(dx1, dy1))))
        hulls.append(place1(helpers.translate(post1, wall_locate2(dx1, dy1))))
        hulls.append(place1(helpers.translate(post1, wall_locate3(dx1, dy1, back))))

        hulls.append(place2(post2))
        hulls.append(place2(helpers.translate(post2, wall_locate1(dx2, dy2))))
        hulls.append(place2(helpers.translate(post2, wall_locate1(dx2, dy2))))
        hulls.append(place2(helpers.translate(post2, wall_locate2(dx2, dy2))))
        hulls.append(place2(helpers.translate(post2, wall_locate3(dx2, dy2, back))))
        shape1 = helpers.hull_from_shapes(hulls)

        hulls = []
        hulls.append(place1(helpers.translate(post1, wall_locate2(dx1, dy1))))
        hulls.append(place1(helpers.translate(post1, wall_locate3(dx1, dy1, back))))
        hulls.append(place2(helpers.translate(post2, wall_locate2(dx2, dy2))))
        hulls.append(place2(helpers.translate(post2, wall_locate3(dx2, dy2, back))))
        shape2 = helpers.bottom_hull(hulls)

        return helpers.union([shape1, shape2])
        # return shape1


    def key_wall_brace(x1, y1, dx1, dy1, post1, x2, y2, dx2, dy2, post2, back=False):
        logger.debug("key_wall_brace()")
        return wall_brace(
            (lambda shape: key_place(shape, x1, y1)),
            dx1,
            dy1,
            post1,
            (lambda shape: key_place(shape, x2, y2)),
            dx2,
            dy2,
            post2,
            back
        )


    def back_wall():
        print("back_wall()")
        x = 0
        shape = helpers.union([key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True)])
        for i in range(settings["ncols"] - 1):
            x = i + 1
            shape = helpers.union([shape, key_wall_brace(x, 0, 0, 1, web_post_tl(), x, 0, 0, 1, web_post_tr(), back=True)])
            shape = helpers.union([shape, key_wall_brace(
                x, 0, 0, 1, web_post_tl(), x - 1, 0, 0, 1, web_post_tr(), back=True
            )])
        shape = helpers.union([shape, key_wall_brace(
            lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr(), back=True
        )])
        return shape


    def right_wall():
        print("right_wall()")

        torow = lastrow - 1

        if (settings["full_last_rows"] or settings["ncols"] < 5):
            torow = lastrow

        tocol = lastcol

        y = 0
        shape = helpers.union([
            key_wall_brace(
                tocol, y, 1, 0, web_post_tr(), tocol, y, 1, 0, web_post_br()
            )
        ])

        for i in range(torow):
            y = i + 1
            shape = helpers.union([shape, key_wall_brace(
                tocol, y - 1, 1, 0, web_post_br(), tocol, y, 1, 0, web_post_tr()
            )])

            shape = helpers.union([shape, key_wall_brace(
                tocol, y, 1, 0, web_post_tr(), tocol, y, 1, 0, web_post_br()
            )])
            # STRANGE PARTIAL OFFSET

        if settings["ncols"] > 4:
            shape = helpers.union([
                shape,
                key_wall_brace(lastcol, torow, 0, -1, web_post_br(), lastcol, torow, 1, 0, web_post_br())
            ])
        return shape


    def left_wall(side='right'):
        print('left_wall()')
        shape = helpers.union([wall_brace(
            (lambda sh: key_place(sh, 0, 0)), 0, 1, web_post_tl(),
            (lambda sh: left_key_place(sh, 0, 1, side=side)), 0, 1, web_post(),
        )])

        shape = helpers.union([shape, wall_brace(
            (lambda sh: left_key_place(sh, 0, 1, side=side)), 0, 1, web_post(),
            (lambda sh: left_key_place(sh, 0, 1, side=side)), -1, 0, web_post(),
        )])

        for i in range(lastrow):
            y = i
            low = (y == (lastrow - 1))
            temp_shape1 = wall_brace(
                (lambda sh: left_key_place(sh, y, 1, side=side)), -1, 0, web_post(),
                (lambda sh: left_key_place(sh, y, -1, low_corner=low, side=side)), -1, 0, web_post(),
            )
            temp_shape2 = helpers.hull_from_shapes((
                key_place(web_post_tl(), 0, y),
                key_place(web_post_bl(), 0, y),
                left_key_place(web_post(), y, 1, side=side),
                left_key_place(web_post(), y, -1, low_corner=low, side=side),
            ))
            shape = helpers.union([shape, temp_shape1])
            shape = helpers.union([shape, temp_shape2])

        for i in range(lastrow - 1):
            y = i + 1
            low = (y == (lastrow - 1))
            temp_shape1 = wall_brace(
                (lambda sh: left_key_place(sh, y - 1, -1, side=side)), -1, 0, web_post(),
                (lambda sh: left_key_place(sh, y, 1, side=side)), -1, 0, web_post(),
            )
            temp_shape2 = helpers.hull_from_shapes((
                key_place(web_post_tl(), 0, y),
                key_place(web_post_bl(), 0, y - 1),
                left_key_place(web_post(), y, 1, side=side),
                left_key_place(web_post(), y - 1, -1, side=side),
                left_key_place(web_post(), y - 1, -1, side=side),
            ))
            shape = helpers.union([shape, temp_shape1])
            shape = helpers.union([shape, temp_shape2])

        return shape


    def front_wall():
        print('front_wall()')

        shape = helpers.union([
            key_wall_brace(
                lastcol, 0, 0, 1, web_post_tr(), lastcol, 0, 1, 0, web_post_tr()
            )
        ])
        shape = helpers.union([shape, key_wall_brace(
            col(3), bottom_key(col(3)), 0, -1, web_post_bl(), col(3), bottom_key(col(3)), 0, -1, web_post_br()
        )])
        # shape = union([key_wall_brace(
        #     col(3), bottom_key(col(3)), 0, -1, web_post_bl(), col(3), bottom_key(col(3)), 0.5, -1, web_post_br()
        # )])
        shape = helpers.union([shape, key_wall_brace(
            col(3), bottom_key(col(3)), 0, -1, web_post_br(), col(4), bottom_key(col(4)), 0.5, -1, web_post_bl()
        )])

        min_last_col = settings["shift_column"] + 2  # first_bottom_key()
        if min_last_col < 0:
            min_last_col = 0
        if min_last_col >= settings["ncols"] - 1:
            min_last_col = settings["ncols"] - 1

        if settings["ncols"] >= min_last_col + 1:
            for i in range(settings["ncols"] - (min_last_col + 1)):
                x = i + min_last_col + 1
                shape = helpers.union([shape, key_wall_brace(
                    x, bottom_key(x), 0, -1, web_post_bl(), x, bottom_key(x), 0, -1, web_post_br()
                )])

        if settings["ncols"] >= min_last_col + 2:
            for i in range(settings["ncols"] - (min_last_col + 2)):
                x = i + (min_last_col + 2)
                shape = helpers.union([shape, key_wall_brace(
                    x, bottom_key(x), 0, -1, web_post_bl(), x - 1, bottom_key(x - 1), 0, -1, web_post_br()
                )])

        return shape


    def case_walls(side='right'):
        print('case_walls()')
        return (
            helpers.union([
                back_wall(),
                left_wall(side=side),
                right_wall(),
                front_wall(),
                cluster(side=side).walls(side=side),
                cluster(side=side).connection(side=side),
            ])
        )


    rj9_start = list(
        np.array([0, -3, 0])
        + np.array(
            key_position(
                list(np.array(wall_locate3(0, 1)) + np.array([0, (mount_height / 2), 0])),
                0,
                0,
            )
        )
    )

    rj9_position = (rj9_start[0], rj9_start[1], 11)


    def rj9_cube():
        logger.debug('rj9_cube()')
        shape = helpers.box(14.78, 13, 22.38)

        return shape


    def rj9_space():
        logger.debug('rj9_space()')
        return helpers.translate(rj9_cube(), rj9_position)


    def rj9_holder():
        print('rj9_holder()')
        shape = helpers.union([helpers.translate(helpers.box(10.78, 9, 18.38), (0, 2, 0)), helpers.translate(helpers.box(10.78, 13, 5), (0, 0, 5))])
        shape = helpers.difference(rj9_cube(), [shape])
        shape = helpers.translate(shape, rj9_position)

        return shape


    usb_holder_position = key_position(
        list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2), 0])), 1, 0
    )
    usb_holder_size = [6.5, 10.0, 13.6]
    usb_holder_thickness = 4


    def usb_holder():
        print('usb_holder()')
        shape = helpers.box(
            usb_holder_size[0] + usb_holder_thickness,
            usb_holder_size[1],
            usb_holder_size[2] + usb_holder_thickness,
        )
        shape = helpers.translate(shape,
                          (
                              usb_holder_position[0],
                              usb_holder_position[1],
                              (usb_holder_size[2] + usb_holder_thickness) / 2,
                          )
                          )
        return shape


    def usb_holder_hole():
        logger.debug('usb_holder_hole()')
        shape = helpers.box(*usb_holder_size)
        shape = helpers.translate(shape,
                          (
                              usb_holder_position[0],
                              usb_holder_position[1],
                              (usb_holder_size[2] + usb_holder_thickness) / 2,
                          )
                          )
        return shape


    def trrs_mount_point():
        shape = helpers.box(6.2, 14, 5.2)
        jack = helpers.translate(helpers.rotate(helpers.cylinder(2.6, 5), (90, 0, 0)), (0, 9, 0))
        jack_entry = helpers.translate(helpers.rotate(helpers.cylinder(4, 5), (90, 0, 0)), (0, 11, 0))
        shape = helpers.rotate(helpers.translate(helpers.union([shape, jack, jack_entry]), (0, 0, 10)), (0, 0, 75))

        # shape = translate(shape,
        #               (
        #                   usb_holder_position[0] + trrs_hole_xoffset,
        #                   usb_holder_position[1] + trrs_hole_yoffset,
        #                   trrs_hole_zoffset,
        #               )
        #               )

        pos = screw_position(0, 0) # wall_locate2(0, 1)
        # trans = wall_locate2(1, 1)
        # pos = [pos[0] + trans[0], pos[1] + trans[1], pos[2]]
        shape = helpers.translate(shape,
                      (
                          pos[0] + settings["trrs_hole_xoffset"],
                          pos[1] + settings["trrs_hole_yoffset"] + settings["screw_offsets"][0][1],
                          settings["trrs_hole_zoffset"],
                      )
                      )
        return shape

    # todo mounts account for walls or walls account for mounts
    def encoder_wall_mount(shape, side='right'):
        pos, rot = oled_position_rotation()

        # hackity hack hack
        if side == 'right':
            pos[0] -= 5
            pos[1] -= 34
            pos[2] -= 7.5
            rot[0] = 0
        else:
            pos[0] -= 3
            pos[1] -= 31
            pos[2] -= 7
            rot[0] = 0
            rot[1] -= 0
            rot[2] = -5

        # enconder_spot = key_position([-10, -5, 13.5], 0, cornerrow)
        ec11_mount = helpers.import_file(path.join(parts_path, "ec11_mount_2"))
        ec11_mount = helpers.translate(helpers.rotate(ec11_mount, rot), pos)
        encoder_cut = helpers.box(10.5, 10.5, 20)
        encoder_cut = helpers.translate(helpers.rotate(encoder_cut, rot), pos)
        shape = helpers.difference(shape, [encoder_cut])
        shape = helpers.union([shape, ec11_mount])
        # encoder_mount = translate(rotate(encoder_mount, (0, 0, 20)), (-27, -4, -15))
        return shape

    def usb_c_shape(width, height, depth):
        shape = helpers.box(width, depth, height)
        cyl1 = helpers.translate(helpers.rotate(helpers.cylinder(height / 2, depth), (90, 0, 0)), (width / 2, 0, 0))
        cyl2 = helpers.translate(helpers.rotate(helpers.cylinder(height / 2, depth), (90, 0, 0)), (-width / 2, 0, 0))
        return helpers.union([shape, cyl1, cyl2])

    def usb_c_hole():
        logger.debug('usb_c_hole()')
        return usb_c_shape(settings["usb_c_width"], settings["usb_c_height"], 20)

    def usb_c_mount_point():
        width = settings["usb_c_width"] * 1.2
        height = settings["usb_c_height"] * 1.2
        front_bit = helpers.translate(usb_c_shape(settings["usb_c_width"] + 2, settings["usb_c_height"] + 2, settings["wall_thickness"] / 2), (0, (settings["wall_thickness"] / 2) + 1, 0))
        shape = helpers.union([front_bit, usb_c_hole()])
        shape = helpers.translate(shape,
                          (
                              usb_holder_position[0] + settings["usb_c_xoffset"],
                              usb_holder_position[1] + settings["usb_c_yoffset"],
                              settings["usb_c_zoffset"],
                          )
                          )
        return shape

    external_start = list(
        # np.array([0, -3, 0])
        np.array([settings["external_holder_width"] / 2, 0, 0])
        + np.array(
            key_position(
                list(np.array(wall_locate3(0, 1)) + np.array([0, (mount_height / 2), 0])),
                0,
                0,
            )
        )
    )

    def blackpill_mount_hole():
        print('blackpill_external_mount_hole()')
        shape = helpers.box(settings["blackpill_holder_width"], 20.0, settings["external_holder_height"] + .1)
        undercut = helpers.box(settings["blackpill_holder_width"] + 8, 10.0, settings["external_holder_height"] + 8 + .1)
        shape = helpers.union([shape, helpers.translate(undercut, (0, -5, 0))])

        shape = helpers.translate(shape,
                          (
                              external_start[0] + settings["blackpill_holder_xoffset"],
                              external_start[1] + settings["external_holder_yoffset"],
                              settings["external_holder_height"] / 2 - .05,
                          )
                          )
        return shape

    def get_logo():
        offset = [
            external_start[0] + settings["external_holder_xoffset"],
            external_start[1] + settings["external_holder_yoffset"] + 4.8,
            settings["external_holder_height"] + 7,
        ]

        logo = helpers.import_file(settings["logo_file"])
        logo = helpers.rotate(logo, (90, 0, 180))
        logo = helpers.translate(logo, offset)
        return logo

    def external_mount_hole():
        print('external_mount_hole()')
        shape = helpers.box(settings["external_holder_width"], 20.0, settings["external_holder_height"] + .1)
        undercut = helpers.box(settings["external_holder_width"] + 8, 10.0, settings["external_holder_height"] + 8 + .1)
        shape = helpers.union([shape, helpers.translate(undercut, (0, -5, 0))])

        shape = helpers.translate(shape,
                          (
                              external_start[0] + settings["external_holder_xoffset"],
                              external_start[1] + settings["external_holder_yoffset"],
                              settings["external_holder_height"] / 2 - .05,
                          )
                          )
        return shape


########### TRACKBALL GENERATION
    def use_btus(cluster):
        return settings["trackball_in_wall"] or (cluster is not None and cluster.has_btus())

    def trackball_cutout(segments=100, side="right"):
        shape = helpers.cylinder(settings["trackball_hole_diameter"] / 2, settings["trackball_hole_height"])
        return shape


    def trackball_socket(btus=False,segments=100, side="right"):
        # shape = sphere(ball_diameter / 2)
        # cyl = cylinder(ball_diameter / 2 + 4, 20)
        # cyl = translate(cyl, (0, 0, -8))
        # shape = union([shape, cyl])

        # tb_file = path.join(parts_path, r"trackball_socket_body_34mm")
        # tbcut_file = path.join(parts_path, r"trackball_socket_cutter_34mm")

        if btus:
            tb_file = path.join(parts_path, r"phat_btu_socket")
            tbcut_file = path.join(parts_path, r"phatter_btu_socket_cutter")
        else:
            tb_file = path.join(parts_path, r"trackball_socket_body_34mm")
            tbcut_file = path.join(parts_path, r"trackball_socket_cutter_34mm")

        if ENGINE == 'cadquery':
            sens_file = path.join(parts_path, r"gen_holder")
        else:
            sens_file = path.join(parts_path, r"trackball_sensor_mount")

        senscut_file = path.join(parts_path, r"trackball_sensor_cutter")

        # shape = import_file(tb_file)
        # # shape = difference(shape, [import_file(senscut_file)])
        # # shape = union([shape, import_file(sens_file)])
        # cutter = import_file(tbcut_file)

        shape = helpers.import_file(tb_file)
        sensor = helpers.import_file(sens_file)
        cutter = helpers.import_file(tbcut_file)
        if not btus:
            cutter = helpers.union([cutter, helpers.import_file(senscut_file)])

        # return shape, cutter
        return shape, cutter, sensor


    def trackball_ball(segments=100, side="right"):
        shape = helpers.sphere(settings["ball_diameter"] / 2)
        return shape

    def generate_trackball(pos, rot, cluster):
        tb_t_offset = settings["tb_socket_translation_offset"]
        tb_r_offset = settings["tb_socket_rotation_offset"]

        if use_btus(cluster):
            tb_t_offset = settings["tb_btu_socket_translation_offset"]
            tb_r_offset = settings["tb_btu_socket_rotation_offset"]

        precut = trackball_cutout()
        precut = helpers.rotate(precut, tb_r_offset)
        precut = helpers.translate(precut, tb_t_offset)
        precut = helpers.rotate(precut, rot)
        precut = helpers.translate(precut, pos)

        shape, cutout, sensor = trackball_socket(btus=use_btus(cluster))

        shape = helpers.rotate(shape, tb_r_offset)
        shape = helpers.translate(shape, tb_t_offset)
        shape = helpers.rotate(shape, rot)
        shape = helpers.translate(shape, pos)

        if cluster is not None and settings["resin"] is False:
            shape = cluster.get_extras(shape, pos)

        cutout = helpers.rotate(cutout, tb_r_offset)
        cutout = helpers.translate(cutout, tb_t_offset)
        # cutout = rotate(cutout, tb_sensor_translation_offset)
        # cutout = translate(cutout, tb_sensor_rotation_offset)
        cutout = helpers.rotate(cutout, rot)
        cutout = helpers.translate(cutout, pos)

        # Small adjustment due to line to line surface / minute numerical error issues
        # Creates small overlap to assist engines in union function later
        sensor = helpers.rotate(sensor, tb_r_offset)
        sensor = helpers.translate(sensor, tb_t_offset)

        # Hackish?  Oh, yes. But it builds with latest cadquery.
        if ENGINE == 'cadquery':
            sensor = helpers.translate(sensor, (0, 0, -15))
        # sensor = rotate(sensor, tb_sensor_translation_offset)
        # sensor = translate(sensor, tb_sensor_rotation_offset)
        sensor = helpers.translate(sensor, (0, 0, .005))
        sensor = helpers.rotate(sensor, rot)
        sensor = helpers.translate(sensor, pos)

        ball = trackball_ball()
        ball = helpers.rotate(ball, tb_r_offset)
        ball = helpers.translate(ball, tb_t_offset)
        ball = helpers.rotate(ball, rot)
        ball = helpers.translate(ball, pos)

        # return precut, shape, cutout, ball
        return precut, shape, cutout, sensor, ball


    def generate_trackball_in_cluster(cluster):
        pos, rot = tbiw_position_rotation()
        if cluster.is_tb:
            pos, rot = cluster.position_rotation()
        return generate_trackball(pos, rot, cluster)


    def tbiw_position_rotation():
        base_pt1 = key_position(
            list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
            0, cornerrow - settings["tbiw_ball_center_row"] - 1
        )
        base_pt2 = key_position(
            list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
            0, cornerrow - settings["tbiw_ball_center_row"] + 1
        )
        base_pt0 = key_position(
            list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])),
            0, cornerrow - settings["tbiw_ball_center_row"]
        )

        left_wall_x_offset = settings["tbiw_left_wall_x_offset_override"]

        tbiw_mount_location_xyz = (
                (np.array(base_pt1) + np.array(base_pt2)) / 2.
                + np.array(((-left_wall_x_offset / 2), 0, 0))
                + np.array(settings["tbiw_translational_offset"])
        )

        # tbiw_mount_location_xyz[2] = (oled_translation_offset[2] + base_pt0[2])/2

        angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
        angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
        tbiw_mount_rotation_xyz = (np.rad2deg(angle_x), 0, np.rad2deg(angle_z)) + np.array(settings["tbiw_rotation_offset"])

        return tbiw_mount_location_xyz, tbiw_mount_rotation_xyz


    def generate_trackball_in_wall():
        pos, rot = tbiw_position_rotation()
        return generate_trackball(pos, rot, None)


    def oled_position_rotation(side='right'):
        wall_x_offsets = get_left_wall_offsets(side)
        _oled_center_row = None
        if settings["trackball_in_wall"] and is_side(side, settings["ball_side"]):
            _oled_center_row = settings["tbiw_oled_center_row"]
            _oled_translation_offset = settings["tbiw_oled_translation_offset"]
            _oled_rotation_offset = settings["tbiw_oled_rotation_offset"]

        elif settings["oled_center_row"] is not None:
            _oled_center_row = settings["oled_center_row"]
            _oled_translation_offset = settings["oled_translation_offset"]
            _oled_rotation_offset = settings["oled_rotation_offset"]

        if _oled_center_row is not None:
            base_pt1 = key_position(
                list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row - 1
            )
            base_pt2 = key_position(
                list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row + 1
            )
            base_pt0 = key_position(
                list(np.array([-mount_width / 2, 0, 0]) + np.array([0, (mount_height / 2), 0])), 0, _oled_center_row
            )

            if settings["oled_horizontal"]:
                _left_wall_x_offset = settings["tbiw_left_wall_x_offset_override"]
            elif (settings["trackball_in_wall"] or settings["oled_horizontal"]) and is_side(side, settings["ball_side"]):
                _left_wall_x_offset = settings["tbiw_left_wall_x_offset_override"]
            else:
                _left_wall_x_offset = wall_x_offsets[0]

            oled_mount_location_xyz = (np.array(base_pt1) + np.array(base_pt2)) / 2. + np.array(
                ((-_left_wall_x_offset / 2), 0, 0)) + np.array(_oled_translation_offset)
            oled_mount_location_xyz[2] = (oled_mount_location_xyz[2] + base_pt0[2]) / 2

            angle_x = np.arctan2(base_pt1[2] - base_pt2[2], base_pt1[1] - base_pt2[1])
            angle_z = np.arctan2(base_pt1[0] - base_pt2[0], base_pt1[1] - base_pt2[1])
            if settings["oled_horizontal"]:
                oled_mount_rotation_xyz = (0, np.rad2deg(angle_x), -100) + np.array(_oled_rotation_offset)
            elif settings["trackball_in_wall"] and is_side(side, settings["ball_side"]):
                # oled_mount_rotation_xyz = (0, np.rad2deg(angle_x), -np.rad2deg(angle_z)-90) + np.array(oled_rotation_offset)
                # oled_mount_rotation_xyz = (np.rad2deg(angle_x)*.707, np.rad2deg(angle_x)*.707, -45) + np.array(oled_rotation_offset)
                oled_mount_rotation_xyz = (0, np.rad2deg(angle_x), -100) + np.array(_oled_rotation_offset)
            else:
                oled_mount_rotation_xyz = (np.rad2deg(angle_x), 0, -np.rad2deg(angle_z)) + np.array(_oled_rotation_offset)

        return oled_mount_location_xyz, oled_mount_rotation_xyz


    def oled_sliding_mount_frame(side='right'):
        mount_ext_width = settings["oled_mount_width"] + 2 * settings["oled_mount_rim"]
        mount_ext_height = (
                settings["oled_mount_height"] + 2 * settings["oled_edge_overlap_end"]
                + settings["oled_edge_overlap_connector"] + settings["oled_edge_overlap_clearance"]
                + 2 * settings["oled_mount_rim"]
        )
        mount_ext_up_height = settings["oled_mount_height"] + 2 * settings["oled_mount_rim"]
        top_hole_start = -mount_ext_height / 2.0 + settings["oled_mount_rim"] + settings["oled_edge_overlap_end"] + settings["oled_edge_overlap_connector"]
        top_hole_length = settings["oled_mount_height"]

        hole = helpers.box(mount_ext_width, mount_ext_up_height, settings["oled_mount_cut_depth"] + .01)
        hole = helpers.translate(hole, (0., top_hole_start + top_hole_length / 2, 0.))

        hole_down = helpers.box(mount_ext_width, mount_ext_height, settings["oled_mount_depth"] + settings["oled_mount_cut_depth"] / 2)
        hole_down = helpers.translate(hole_down, (0., 0., -settings["oled_mount_cut_depth"] / 4))
        hole = helpers.union([hole, hole_down])

        shape = helpers.box(mount_ext_width, mount_ext_height, settings["oled_mount_depth"])

        conn_hole_start = (-mount_ext_height / 2.0 + settings["oled_mount_rim"]) - 2
        conn_hole_length = (
                settings["oled_edge_overlap_end"] + settings["oled_edge_overlap_connector"]
                + settings["oled_edge_overlap_clearance"] + settings["oled_thickness"]
        ) + 4
        conn_hole = helpers.box(settings["oled_mount_width"], conn_hole_length + .01, settings["oled_mount_depth"])
        conn_hole = helpers.translate(conn_hole, (
            0,
            conn_hole_start + conn_hole_length / 2,
            -settings["oled_edge_overlap_thickness"]
        ))

        end_hole_length = (
                settings["oled_edge_overlap_end"] + settings["oled_edge_overlap_clearance"]
        )
        end_hole_start = mount_ext_height / 2.0 - settings["oled_mount_rim"] - end_hole_length
        end_hole = helpers.box(settings["oled_mount_width"], end_hole_length + .01, settings["oled_mount_depth"])
        end_hole = helpers.translate(end_hole, (
            0,
            end_hole_start + end_hole_length / 2,
            -settings["oled_edge_overlap_thickness"]
        ))

        top_hole_start = -mount_ext_height / 2.0 + settings["oled_mount_rim"] + settings["oled_edge_overlap_end"] + settings["oled_edge_overlap_connector"]
        top_hole_length = settings["oled_mount_height"]
        top_hole = helpers.box(settings["oled_mount_width"], top_hole_length, settings["oled_edge_overlap_thickness"] + settings["oled_thickness"] - settings["oled_edge_chamfer"])
        top_hole = helpers.translate(top_hole, (
            0,
            top_hole_start + top_hole_length / 2,
            (settings["oled_mount_depth"] - settings["oled_edge_overlap_thickness"] - settings["oled_thickness"] - settings["oled_edge_chamfer"]) / 2.0
        ))

        top_chamfer_1 = helpers.box(
            settings["oled_mount_width"],
            top_hole_length,
            0.01
        )
        top_chamfer_2 = helpers.box(
            settings["oled_mount_width"] + 2 * settings["oled_edge_chamfer"],
            top_hole_length + 2 * settings["oled_edge_chamfer"],
            0.01
        )
        top_chamfer_1 = helpers.translate(top_chamfer_1, (0, 0, -settings["oled_edge_chamfer"] - .05))

        top_chamfer_1 = helpers.hull_from_shapes([top_chamfer_1, top_chamfer_2])

        top_chamfer_1 = helpers.translate(top_chamfer_1, (
            0,
            top_hole_start + top_hole_length / 2,
            settings["oled_mount_depth"] / 2.0 + .05
        ))

        top_hole = helpers.union([top_hole, top_chamfer_1])

        shape = helpers.difference(shape, [conn_hole, top_hole, end_hole])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = helpers.rotate(shape, oled_mount_rotation_xyz)
        shape = helpers.translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = helpers.rotate(hole, oled_mount_rotation_xyz)
        hole = helpers.translate(hole,
                         (
                             oled_mount_location_xyz[0],
                             oled_mount_location_xyz[1],
                             oled_mount_location_xyz[2],
                         )
                         )
        return hole, shape


    def oled_clip_mount_frame(side='right'):
        mount_ext_width = settings["oled_mount_width"] + 2 * settings["oled_mount_rim"]
        mount_ext_height = (
                settings["oled_mount_height"] + 2 * settings["oled_clip_thickness"]
                + 2 * settings["oled_clip_undercut"] + 2 * settings["oled_clip_overhang"] + 2 * settings["oled_mount_rim"]
        )
        hole = helpers.box(mount_ext_width, mount_ext_height, settings["oled_mount_cut_depth"] + .01)

        shape = helpers.box(mount_ext_width, mount_ext_height, settings["oled_mount_depth"])
        shape = helpers.difference(shape, [helpers.box(settings["oled_mount_width"], settings["oled_mount_height"], settings["oled_mount_depth"] + .1)])

        clip_slot = helpers.box(
            settings["oled_clip_width"] + 2 * settings["oled_clip_width_clearance"],
            settings["oled_mount_height"] + 2 * settings["oled_clip_thickness"] + 2 * settings["oled_clip_overhang"],
            settings["oled_mount_depth"] + .1
        )

        shape = helpers.difference(shape, [clip_slot])

        clip_undercut = helpers.box(
            settings["oled_clip_width"] + 2 * settings["oled_clip_width_clearance"],
            settings["oled_mount_height"] + 2 * settings["oled_clip_thickness"] + 2 * settings["oled_clip_overhang"] + 2 * settings["oled_clip_undercut"],
            settings["oled_mount_depth"] + .1
        )

        clip_undercut = helpers.translate(clip_undercut, (0., 0., settings["oled_clip_undercut_thickness"]))
        shape = helpers.difference(shape, [clip_undercut])

        plate = helpers.box(
            settings["oled_mount_width"] + .1,
            settings["oled_mount_height"] - 2 * settings["oled_mount_connector_hole"],
            settings["oled_mount_depth"] - settings["oled_thickness"]
        )
        plate = helpers.translate(plate, (0., 0., -settings["oled_thickness"] / 2.0))
        shape = helpers.union([shape, plate])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = helpers.rotate(shape, oled_mount_rotation_xyz)
        shape = helpers.translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = helpers.rotate(hole, oled_mount_rotation_xyz)
        hole = helpers.translate(hole,
                         (
                             oled_mount_location_xyz[0],
                             oled_mount_location_xyz[1],
                             oled_mount_location_xyz[2],
                         )
                         )

        return hole, shape


    def oled_clip():
        mount_ext_width = settings["oled_mount_width"] + 2 * settings["oled_mount_rim"]
        mount_ext_height = (
                settings["oled_mount_height"] + 2 * settings["oled_clip_thickness"] + 2 * settings["oled_clip_overhang"]
                + 2 * settings["oled_clip_undercut"] + 2 * settings["oled_mount_rim"]
        )

        oled_leg_depth = settings["oled_mount_depth"] + settings["oled_clip_z_gap"]

        shape = helpers.box(mount_ext_width - .1, mount_ext_height - .1, settings["oled_mount_bezel_thickness"])
        shape = helpers.translate(shape, (0., 0., settings["oled_mount_bezel_thickness"] / 2.))

        hole_1 = helpers.box(
            settings["oled_screen_width"] + 2 * settings["oled_mount_bezel_chamfer"],
            settings["oled_screen_length"] + 2 * settings["oled_mount_bezel_chamfer"],
            .01
        )
        hole_2 = helpers.box(settings["oled_screen_width"], settings["oled_screen_length"], 2.05 * settings["oled_mount_bezel_thickness"])
        hole = helpers.hull_from_shapes([hole_1, hole_2])

        shape = helpers.difference(shape, [helpers.translate(hole, (0., 0., settings["oled_mount_bezel_thickness"]))])

        clip_leg = helpers.box(settings["oled_clip_width"], settings["oled_clip_thickness"], oled_leg_depth)
        clip_leg = helpers.translate(clip_leg, (
            0.,
            0.,
            # (oled_mount_height+2*oled_clip_overhang+oled_clip_thickness)/2,
            -oled_leg_depth / 2.
        ))

        latch_1 = helpers.box(
            settings["oled_clip_width"],
            settings["oled_clip_overhang"] + settings["oled_clip_thickness"],
            .01
        )
        latch_2 = helpers.box(
            settings["oled_clip_width"],
            settings["oled_clip_thickness"] / 2,
            settings["oled_clip_extension"]
        )
        latch_2 = helpers.translate(latch_2, (
            0.,
            -(-settings["oled_clip_thickness"] / 2 + settings["oled_clip_thickness"] + settings["oled_clip_overhang"]) / 2,
            -settings["oled_clip_extension"] / 2
        ))
        latch = helpers.hull_from_shapes([latch_1, latch_2])
        latch = helpers.translate(latch, (
            0.,
            settings["oled_clip_overhang"] / 2,
            -oled_leg_depth
        ))

        clip_leg = helpers.union([clip_leg, latch])

        clip_leg = helpers.translate(clip_leg, (
            0.,
            (settings["oled_mount_height"] + 2 * settings["oled_clip_overhang"] + settings["oled_clip_thickness"]) / 2 - settings["oled_clip_y_gap"],
            0.
        ))

        shape = helpers.union([shape, clip_leg, helpers.mirror(clip_leg, 'XZ')])

        return shape


    def oled_undercut_mount_frame(side='right'):
        mount_ext_width = settings["oled_mount_width"] + 2 * settings["oled_mount_rim"]
        mount_ext_height = settings["oled_mount_height"] + 2 * settings["oled_mount_rim"]
        hole = helpers.box(mount_ext_width, mount_ext_height, settings["oled_mount_cut_depth"] + .01)

        shape = helpers.box(mount_ext_width, mount_ext_height, settings["oled_mount_depth"])
        shape = helpers.difference(shape, [helpers.box(settings["oled_mount_width"], settings["oled_mount_height"], settings["oled_mount_depth"] + .1)])
        undercut = helpers.box(
            settings["oled_mount_width"] + 2 * settings["oled_mount_undercut"],
            settings["oled_mount_height"] + 2 * settings["oled_mount_undercut"],
            settings["oled_mount_depth"])
        undercut = helpers.translate(undercut, (0., 0., -settings["oled_mount_undercut_thickness"]))
        shape = helpers.difference(shape, [undercut])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = helpers.rotate(shape, oled_mount_rotation_xyz)
        shape = helpers.translate(shape, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                          )

        hole = helpers.rotate(hole, oled_mount_rotation_xyz)
        hole = helpers.translate(hole, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                         )

        return hole, shape


    def teensy_holder():
        print('teensy_holder()')
        teensy_top_xy = key_position(wall_locate3(-1, 0), 0, centerrow - 1)
        teensy_bot_xy = key_position(wall_locate3(-1, 0), 0, centerrow + 1)
        teensy_holder_length = teensy_top_xy[1] - teensy_bot_xy[1]
        teensy_holder_offset = -teensy_holder_length / 2
        teensy_holder_top_offset = (teensy_holder_top_length / 2) - teensy_holder_length

        s1 = helpers.box(3, teensy_holder_length, 6 + teensy_width)
        s1 = helpers.translate(s1, [1.5, teensy_holder_offset, 0])

        s2 = helpers.box(teensy_pcb_thickness, teensy_holder_length, 3)
        s2 = helpers.translate(s2,
                       (
                           (teensy_pcb_thickness / 2) + 3,
                           teensy_holder_offset,
                           -1.5 - (teensy_width / 2),
                       )
                       )

        s3 = helpers.box(teensy_pcb_thickness, teensy_holder_top_length, 3)
        s3 = helpers.translate(s3,
                       [
                           (teensy_pcb_thickness / 2) + 3,
                           teensy_holder_top_offset,
                           1.5 + (teensy_width / 2),
                       ]
                       )

        s4 = helpers.box(4, teensy_holder_top_length, 4)
        s4 = helpers.translate(s4,
                       [teensy_pcb_thickness + 5, teensy_holder_top_offset, 1 + (teensy_width / 2)]
                       )

        shape = helpers.union((s1, s2, s3, s4))

        shape = helpers.translate(shape, [-teensy_holder_width, 0, 0])
        shape = helpers.translate(shape, [-1.4, 0, 0])
        shape = helpers.translate(shape,
                          [teensy_top_xy[0], teensy_top_xy[1] - 1, (6 + teensy_width) / 2]
                          )

        return shape

    def brass_insert_hole(radii=(2.4, 2.4), heights=(3, 1.5), scale_by=1):
        if len(radii) != len(heights):
            raise Exception("radii and heights collections must have equal length")

        total_height = sum(heights) + 0.2  # add 0.3 for a titch extra

        half_height = total_height / 2
        offset = half_height
        cyl = None
        for i in range(len(radii)):
            radius = radii[i] * scale_by
            height = heights[i]
            offset -= height / 2
            new_cyl = helpers.translate(helpers.cylinder(radius, height), (0, 0, offset))
            if cyl is None:
                cyl = new_cyl
            else:
                cyl = helpers.union([cyl, new_cyl])
            offset -= height / 2
        cyl = helpers.translate(helpers.rotate(cyl, (0, 180, 0)), (0, 0, -0.01))
        return cyl, sum(heights)


    def screw_insert_shape(bottom_radius, top_radius, height, hole=False):
        logger.debug('screw_insert_shape()')
        mag_offset = 0
        new_height = height
        if hole:
            scale = 1.0 if settings["resin"] else 0.95
            shape, new_height = brass_insert_hole(scale_by=scale)
            new_height -= 1
        else:
            if bottom_radius == top_radius:
                shape = helpers.translate(helpers.cylinder(radius=bottom_radius, height=new_height),
                                 (0, 0, mag_offset - (new_height / 2))  # offset magnet by 1 mm in case
                                 )
            else:
                shape = helpers.translate(helpers.cone(r1=bottom_radius, r2=top_radius, height=new_height), (0, 0, -new_height / 2))

        if settings["magnet_bottom"]:
            if not hole:
                shape = helpers.union((
                    shape,
                    helpers.translate(helpers.sphere(top_radius), (0, 0, mag_offset / 2)),
                ))
        else:
            shape = helpers.union((
                shape,
                helpers.translate(helpers.sphere(top_radius), (0, 0,  (new_height / 2))),
            ))
        return shape

    def screw_insert(column, row, bottom_radius, top_radius, height, side='right', hole=False):
        logger.debug('screw_insert()')
        position = screw_position(column, row, side)
        shape = screw_insert_shape(bottom_radius, top_radius, height, hole=hole)
        shape = helpers.translate(shape, [position[0], position[1], height / 2])

        return shape

    def screw_position(column, row,  side='right'):
        logger.debug('screw_position()')
        shift_right = column == lastcol
        shift_left = column == 0
        shift_up = (not (shift_right or shift_left)) and (row == 0)
        shift_down = (not (shift_right or shift_left)) and (row >= lastrow)

        if settings["screws_offset"] == 'INSIDE':
            # logger.debug('Shift Inside')
            shift_left_adjust = settings["wall_base_x_thickness"]
            shift_right_adjust = -settings["wall_base_x_thickness"] / 3
            shift_down_adjust = -settings["wall_base_y_thickness"] / 2
            shift_up_adjust = -settings["wall_base_y_thickness"] / 3

        elif settings["screws_offset"] == 'OUTSIDE':
            logger.debug('Shift Outside')
            shift_left_adjust = 0
            shift_right_adjust = settings["wall_base_x_thickness"] / 2
            shift_down_adjust = settings["wall_base_y_thickness"] * 2 / 3
            shift_up_adjust = settings["wall_base_y_thickness"] * 2 / 3

        else:
            # logger.debug('Shift Origin')
            shift_left_adjust = 0
            shift_right_adjust = 0
            shift_down_adjust = 0
            shift_up_adjust = 0

        if shift_up:
            position = key_position(
                list(np.array(wall_locate2(0, 1)) + np.array([0, (mount_height / 2) + shift_up_adjust, 0])),
                column,
                row,
            )
        elif shift_down:
            position = key_position(
                list(np.array(wall_locate2(0, -1)) - np.array([0, (mount_height / 2) + shift_down_adjust, 0])),
                column,
                row,
            )
        elif shift_left:
            position = list(
                np.array(left_key_position(row, 0, side=side)) + np.array(wall_locate3(-1, 0)) + np.array(
                    (shift_left_adjust, 0, 0))
            )
        else:
            position = key_position(
                list(np.array(wall_locate2(1, 0)) + np.array([(mount_height / 2), 0, 0]) + np.array(
                    (shift_right_adjust, 0, 0))
                     ),
                column,
                row,
            )

        return position

    def screw_insert_thumb(bottom_radius, top_radius, top_height, hole=False, side="right"):
        position = cluster(side).screw_positions()
        shape = screw_insert_shape(bottom_radius, top_radius, top_height, hole=hole)
        shape = helpers.translate(shape, [position[0], position[1], top_height / 2])
        return shape


    def screw_insert_all_shapes(bottom_radius, top_radius, height, offset=0, side='right', hole=False):
        print('screw_insert_all_shapes()')
        so = settings["screw_offsets"]
        shape = (
            helpers.translate(screw_insert(0, 0, bottom_radius, top_radius, height, side=side, hole=hole), (so[0][0], so[0][1], so[0][2] + offset)),  # rear left
            helpers.translate(screw_insert(0, lastrow - 1, bottom_radius, top_radius, height, side=side, hole=hole), (so[1][0], so[1][1] + left_wall_lower_y_offset, so[1][2] + offset)),  # front left
            helpers.translate(screw_insert(3, lastrow, bottom_radius, top_radius, height, side=side, hole=hole), (so[2][0], so[2][1], so[2][2] + offset)),  # front middle
            helpers.translate(screw_insert(3, 0, bottom_radius, top_radius, height, side=side, hole=hole), (so[3][0], so[3][1], so[3][2] + offset)),  # rear middle
            helpers.translate(screw_insert(lastcol, 0, bottom_radius, top_radius, height, side=side, hole=hole), (so[4][0], so[4][1], so[4][2] + offset)),  # rear right
            helpers.translate(screw_insert(lastcol, lastrow - 1, bottom_radius, top_radius, height, side=side, hole=hole), (so[5][0], so[5][1], so[5][2] + offset)),  # front right
            helpers.translate(screw_insert_thumb(bottom_radius, top_radius, height, side=side, hole=hole), (so[6][0], so[6][1], so[6][2] + offset)),  # thumb cluster
        )

        return shape


    def screw_insert_holes(side='right'):
        return screw_insert_all_shapes(
            settings["screw_insert_bottom_radius"], settings["screw_insert_top_radius"], settings["screw_insert_height"] + .02, offset=-.01, side=side, hole=True
        )


    def screw_insert_outers(side='right'):
        return screw_insert_all_shapes(
            settings["screw_insert_bottom_radius"] + 1.6,
            settings["screw_insert_top_radius"] + 1.6,
            settings["screw_insert_height"] + 1.5,
            side=side
        )


    def screw_insert_screw_holes(side='right'):
        return screw_insert_all_shapes(1.7, 1.7, 350, side=side)


    def wire_post(direction, offset):
        logger.debug('wire_post()')
        s1 = helpers.box(
            settings["wire_post_diameter"], settings["wire_post_diameter"], settings["wire_post_height"]
        )
        s1 = helpers.translate(s1, [0, -settings["wire_post_diameter"] * 0.5 * direction, 0])

        s2 = helpers.box(
            settings["wire_post_diameter"], settings["wire_post_overhang"], settings["wire_post_diameter"]
        )
        s2 = helpers.translate(s2,
                       [0, -settings["wire_post_overhang"] * 0.5 * direction, -settings["wire_post_height"] / 2]
                       )

        shape = helpers.union((s1, s2))
        shape = helpers.translate(shape, [0, -offset, (-settings["wire_post_height"] / 2) + 3])
        shape = helpers.rotate(shape, [-settings["alpha"] / 2, 0, 0])
        shape = helpers.translate(shape, (3, -mount_height / 2, 0))

        return shape

    def model_side(side="right"):
        print('model_side()' + side)
        shape = helpers.union([key_holes(side=side)])
        if debug_exports:
            helpers.export_file(shape=shape, fname=path.join(r".", "things", r"debug_key_plates"))
        connector_shape = connectors()
        shape = helpers.union([shape, connector_shape])
        if debug_exports:
            helpers.export_file(shape=shape, fname=path.join(r".", "things", r"debug_connector_shape"))
        thumb_shape = cluster(side).thumb(side=side)
        if debug_exports:
            helpers.export_file(shape=thumb_shape, fname=path.join(r".", "things", r"debug_thumb_shape"))
        shape = helpers.union([shape, thumb_shape])
        thumb_connector_shape = cluster(side).thumb_connectors(side=side)
        shape = helpers.union([shape, thumb_connector_shape])
        if debug_exports:
            helpers.export_file(shape=shape, fname=path.join(r".", "things", r"debug_thumb_connector_shape"))
        walls_shape = case_walls(side=side)
        if debug_exports:
            helpers.export_file(shape=walls_shape, fname=path.join(r".", "things", r"debug_walls_shape"))
        s2 = helpers.union([walls_shape])
        s2 = helpers.union([s2, *screw_insert_outers(side=side)])

        if trrs_hole:
            s2 = helpers.difference(s2, [trrs_mount_point()])

        if is_side(side, settings["controller_side"]):
            if settings["controller_mount_type"] in ['RJ9_USB_TEENSY', 'USB_TEENSY']:
                s2 = helpers.union([s2, teensy_holder()])

            if settings["controller_mount_type"] in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL', 'USB_WALL', 'USB_TEENSY']:
                s2 = helpers.union([s2, usb_holder()])
                s2 = helpers.difference(s2, [usb_holder_hole()])

            if settings["controller_mount_type"] in ['USB_C_WALL']:
                s2 = helpers.difference(s2, [usb_c_mount_point()])

            if settings["controller_mount_type"] in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
                s2 = helpers.difference(s2, [rj9_space()])

            if settings["controller_mount_type"] in ['BLACKPILL_EXTERNAL']:
                s2 = helpers.difference(s2, [blackpill_mount_hole()])

            if settings["controller_mount_type"] in ['EXTERNAL']:
                s2 = helpers.difference(s2, [external_mount_hole()])

            if settings["controller_mount_type"] in ['None']:
                0  # do nothing, only here to expressly state inaction.

        s2 = helpers.difference(s2, [helpers.union(screw_insert_holes(side=side))])

        if side == "right" and settings["logo_file"] not in ["", None]:
            s2 = helpers.union([s2, get_logo()])

        shape = helpers.union([shape, s2])

        if settings["controller_mount_type"] in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
            shape = helpers.union([shape, rj9_holder()])

        if is_oled(side):
            if settings["oled_mount_type"] == "UNDERCUT":
                hole, frame = oled_undercut_mount_frame(side=side)
                shape = helpers.difference(shape, [hole])
                shape = helpers.union([shape, frame])

            elif settings["oled_mount_type"] == "SLIDING":
                hole, frame = oled_sliding_mount_frame(side=side)
                shape = helpers.difference(shape, [hole])
                shape = helpers.union([shape, frame])
                if settings["encoder_in_wall"]:
                    shape = encoder_wall_mount(shape, side)

            elif settings["oled_mount_type"] == "CLIP":
                hole, frame = oled_clip_mount_frame(side=side)
                shape = helpers.difference(shape, [hole])
                shape = helpers.union([shape, frame])

        if not quickly:
            if settings["trackball_in_wall"] and is_side(side, settings["ball_side"]):
                tbprecut, tb, tbcutout, sensor, ball = generate_trackball_in_wall()

                shape = helpers.difference(shape, [tbprecut])
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
                shape = helpers.union([shape, tb])
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
                shape = helpers.difference(shape, [tbcutout])
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
                # export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
                shape = helpers.union([shape, sensor])

                if settings["show_caps"]:
                    shape = helpers.add([shape, ball])

            elif cluster(side).is_tb:
                tbprecut, tb, tbcutout, sensor, ball = generate_trackball_in_cluster(cluster(side))

                shape = helpers.difference(shape, [tbprecut])
                if cluster(side).has_btus():
                    shape = helpers.difference(shape, [tbcutout])
                    shape = helpers.union([shape, tb])
                else:
                    # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
                    shape = helpers.union([shape, tb])
                    # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
                    shape = helpers.difference(shape, [tbcutout])
                    # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
                    # export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
                    shape = helpers.union([shape, sensor])

                if settings["show_caps"]:
                    shape = helpers.add([shape, ball])

        block = helpers.translate(helpers.box(400, 400, 40), (0, 0, -20))
        shape = helpers.difference(shape, [block])

        if settings["show_caps"]:
            shape = helpers.add([shape, cluster(side).thumbcaps(side=side)])
            shape = helpers.add([shape, caps()])

        if side == "left":
            shape = helpers.mirror(shape, 'YZ')

        return shape, walls_shape

    def wrist_rest(base, plate, side="right"):
        rest = helpers.import_file(path.join(parts_path, "dactyl_wrist_rest_v3_" + side))
        rest = helpers.rotate(rest, (0, 0, -60))
        rest = helpers.translate(rest, (30, -150, 26))
        rest = helpers.union([rest, helpers.translate(base, (0, 0, 5)), plate])
        return rest

    # NEEDS TO BE SPECIAL FOR CADQUERY
    def baseplate(shape, wedge_angle=None, side='right'):
        global logo_file
        if ENGINE == 'cadquery':
            # shape = mod_r
            shape = helpers.union([shape, *screw_insert_outers(side=side)])
            # tool = translate(screw_insert_screw_holes(side=side), [0, 0, -10])
            if settings["magnet_bottom"]:
                tool = screw_insert_all_shapes(settings["screw_hole_diameter"] / 2., settings["screw_hole_diameter"] / 2., 2.1, side=side)
                for item in tool:
                    item = helpers.translate(item, [0, 0, 1.2])
                    shape = helpers.difference(shape, [item])
            else:
                tool = screw_insert_all_shapes(settings["screw_hole_diameter"] / 2., settings["screw_hole_diameter"] / 2., 350, side=side)
                for item in tool:
                    item = helpers.translate(item, [0, 0, -10])
                    shape = helpers.difference(shape, [item])

            shape = helpers.translate(shape, (0, 0, -0.0001))

            square = cq.Workplane('XY').rect(1000, 1000)
            for wire in square.wires().objects:
                plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))
            shape = helpers.intersect(shape, plane)

            outside = shape.vertices(cq.DirectionMinMaxSelector(cq.Vector(1, 0, 0), True)).objects[0]
            sizes = []
            max_val = 0
            inner_index = 0
            base_wires = shape.wires().objects
            for i_wire, wire in enumerate(base_wires):
                is_outside = False
                for vert in wire.Vertices():
                    if vert.toTuple() == outside.toTuple():
                        outer_wire = wire
                        outer_index = i_wire
                        is_outside = True
                        sizes.append(0)
                if not is_outside:
                    sizes.append(len(wire.Vertices()))
                if sizes[-1] > max_val:
                    inner_index = i_wire
                    max_val = sizes[-1]
            logger.debug(sizes)
            inner_wire = base_wires[inner_index]

            # inner_plate = cq.Workplane('XY').add(cq.Face.makeFromWires(inner_wire))
            if wedge_angle is not None:
                cq.Workplane('XY').add(cq.Solid.revolve(outerWire, innerWires, angleDegrees, axisStart, axisEnd))
            else:
                inner_shape = cq.Workplane('XY').add(
                    cq.Solid.extrudeLinear(inner_wire, [], cq.Vector(0, 0, settings["base_thickness"])))
                inner_shape = helpers.translate(inner_shape, (0, 0, -settings["base_rim_thickness"]))
                if settings["block_bottoms"]:
                    inner_shape = blockerize(inner_shape)
                if settings["logo_file"] not in ["", None]:
                    logo_offset = [
                        -10,
                        -10,
                        -0.5
                    ]
                    logo = helpers.import_file(logo_file)
                    if side == "left":
                        logo = helpers.mirror(logo, "YZ")
                    if settings["ncols"] <= 6:
                        logo_offset[0] -= 12 * (7 - settings["ncols"])
                    if settings["nrows"] <= 5:
                        logo_offset[1] += 15 * (6 - settings["ncols"])
                    logo = helpers.translate(logo, logo_offset)

                    inner_shape = helpers.union([inner_shape, logo])

                holes = []
                for i in range(len(base_wires)):
                    if i not in [inner_index, outer_index]:
                        holes.append(base_wires[i])
                cutout = [*holes, inner_wire]

                shape = cq.Workplane('XY').add(
                    cq.Solid.extrudeLinear(outer_wire, cutout, cq.Vector(0, 0, settings["base_rim_thickness"])))
                hole_shapes = []
                for hole in holes:
                    loc = hole.Center()
                    hole_shapes.append(
                        helpers.translate(
                            helpers.cylinder(settings["screw_cbore_diameter"] / 2.0, settings["screw_cbore_depth"]),
                            (loc.x, loc.y, 0)
                            # (loc.x, loc.y, screw_cbore_depth/2)
                        )
                    )
                shape = helpers.difference(shape, hole_shapes)
                shape = helpers.translate(shape, (0, 0, -settings["base_rim_thickness"]))
                shape = helpers.union([shape, inner_shape])
                if magnet_bottom:
                    shape = helpers.difference(shape, [helpers.translate(magnet, (0, 0, 0.05 - (settings["screw_insert_height"] / 2))) for magnet in list(tool)])

            return shape
        else:

            shape = helpers.union([
                case_walls(side=side),
                *screw_insert_outers(side=side)
            ])

            tool = helpers.translate(helpers.union(screw_insert_screw_holes(side=side)), [0, 0, -10])
            base = helpers.box(1000, 1000, .01)
            shape = shape - tool
            shape = helpers.intersect(shape, base)

            shape = helpers.translate(shape, [0, 0, -0.001])

            return sl.projection(cut=True)(shape)


    def run():
        mod_r, walls_r = model_side(side="right")
        if settings["resin"] and ENGINE == "cadquery":
            mod_r = helpers.rotate(mod_r, (333.04, 43.67, 85.00))
        helpers.export_file(shape=mod_r, fname=path.join(save_path, r_config_name + r"_right"))

        if settings["right_side_only"]:
            print(">>>>>  RIGHT SIDE ONLY: Only rendering a the right side.")
            return
        base = baseplate(walls_r, side='right')
        helpers.export_file(shape=base, fname=path.join(save_path, r_config_name + r"_right_plate"))
        if quickly:
            print(">>>>>  QUICK RENDER: Only rendering a the right side and bottom plate.")
            return
        helpers.export_dxf(shape=base, fname=path.join(save_path, r_config_name + r"_right_plate"))

        # rest = wrist_rest(mod_r, base, side="right")
        #
        # export_file(shape=rest, fname=path.join(save_path, config_name + r"_right_wrist_rest"))

        # if symmetry == "asymmetric":

        mod_l, walls_l = model_side(side="left")
        if settings["resin"] and ENGINE == "cadquery":
            mod_l = helpers.rotate(mod_l, (333.04, 317.33, 286.35))
        helpers.export_file(shape=mod_l, fname=path.join(save_path, l_config_name + r"_left"))

        base_l = helpers.mirror(baseplate(walls_l, side='left'), 'YZ')
        helpers.export_file(shape=base_l, fname=path.join(save_path, l_config_name + r"_left_plate"))
        helpers.export_dxf(shape=base_l, fname=path.join(save_path, l_config_name + r"_left_plate"))

        # else:
        #     export_file(shape=mirror(mod_r, 'YZ'), fname=path.join(save_path, config_name + r"_left"))
        #
        #     lbase = mirror(base, 'YZ')
        #     export_file(shape=lbase, fname=path.join(save_path, config_name + r"_left_plate"))
        #     export_dxf(shape=lbase, fname=path.join(save_path, config_name + r"_left_plate"))

        if ENGINE == 'cadquery' and overrides_name not in [None, '']:
            import build_report as report
            report.write_build_report(path.abspath(save_path), overrides_name, git_data)

        # if oled_mount_type == 'UNDERCUT':
        #     export_file(shape=oled_undercut_mount_frame()[1],
        #                 fname=path.join(save_path, config_name + r"_oled_undercut_test"))
        #
        # if oled_mount_type == 'SLIDING':
        #     export_file(shape=oled_sliding_mount_frame()[1],
        #                 fname=path.join(save_path, config_name + r"_oled_sliding_test"))

        if settings["oled_mount_type"] == 'CLIP':
            oled_mount_location_xyz = (0.0, 0.0, -settings["oled_mount_depth"] / 2)
            oled_mount_rotation_xyz = (0.0, 0.0, 0.0)
            helpers.export_file(shape=oled_clip(), fname=path.join(save_path, config_name + r"_oled_clip"))
            # export_file(shape=oled_clip_mount_frame()[1],
            #             fname=path.join(save_path, config_name + r"_oled_clip_test"))
            # export_file(shape=union((oled_clip_mount_frame()[1], oled_clip())),
            #             fname=path.join(save_path, config_name + r"_oled_clip_assy_test"))

    def get_cluster(style):
        if style == CarbonfetCluster.name:
            clust = CarbonfetCluster(settings, helpers)
        elif style == MiniCluster.name:
            clust = MiniCluster(settings, helpers)
        elif style == MinidoxCluster.name:
            clust = MinidoxCluster(settings, helpers)
        elif style == Minithicc.name:
            clust = Minithicc(settings, helpers)
        elif style == Minithicc3.name:
            clust = Minithicc3(settings, helpers)
        elif style == TrackballOrbyl.name:
            clust = TrackballOrbyl(settings, helpers)
        elif style == TrackballWild.name:
            clust = TrackballWild(settings, helpers)
        elif style == TrackballThree.name:
            clust = TrackballThree(settings, helpers)
        elif style == TrackballBTU.name:
            clust = TrackballBTU(settings, helpers)
        elif style == TrackballCJ.name:
            clust = TrackballCJ(settings, helpers)
        elif style == CustomCluster.name:
            clust = CustomCluster(settings, helpers)
        else:
            clust = DefaultCluster(settings, helpers)

        return clust


    right_cluster = get_cluster(settings["thumb_style"])

    if right_cluster.is_tb:
        if settings["ball_side"] == "both":
            left_cluster = right_cluster
        elif settings["ball_side"] == "left":
            left_cluster = right_cluster
            right_cluster = get_cluster(settings["other_thumb"])
        else:
            left_cluster = get_cluster(settings["other_thumb"])
    elif settings["other_thumb"] != "DEFAULT" and settings["other_thumb"] != settings["thumb_style"]:
        left_cluster = get_cluster(settings["other_thumb"])
    else:
        left_cluster = right_cluster  # this assumes thumb_style always overrides DEFAULT other_thumb

    run()


#
if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="Dactyl Keyboard Generator", description="Generates models for DM")
    parser.add_argument("-c", "--config", dest="config", help="pass a named config file")
    parser.add_argument("-o", "--output", dest="output", help="use a different output directory")
    parser.add_argument("-O", "--overrides", dest="overrides", help="pass overrides in cli")
    args = parser.parse_args()

    make_dactyl(args)

    # base = baseplate()
    # export_file(shape=base, fname=path.join(save_path, config_name + r"_plate"))

