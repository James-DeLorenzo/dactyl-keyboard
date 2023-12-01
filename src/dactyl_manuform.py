import argparse
import git
import json
import os
import sys
import time
import logging

import numpy as np
from os import path
import os.path as path
import cadquery as cq

from json_loader import load_json
from helper import Helper
from clusters import Cluster
from utils import CapBuilder, connectors, walls


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

# class FileFormatter(logging.Formatter):
#     def format(self, record):
#         # Add the file name to the log record
#         record.file_name = record.pathname.split('/')[-1]
#         return super(FileFormatter, self).format(record)
#
# # Create a logger
# logger = logging.getLogger(__name__)
#
# # Create a file handler and set the formatter
# file_handler = logging.FileHandler('example.log')
# file_formatter = FileFormatter(fmt='%(asctime)s - %(file_name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# file_handler.setFormatter(file_formatter)
#
# # Add the file handler to the logger
# logger.addHandler(file_handler)
#
# # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# logger.setLevel(logging.DEBUG)
logging.basicConfig(level=os.environ.get("LOG_LEVEL",logging.INFO), format="%(levelname)s:%(filename)s:%(funcName)s:%(message)s")
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


    right_cluster: Cluster = None
    left_cluster: Cluster = None

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
        with open(os.path.join(r".", "configs", f"{args.config}.json"), mode='r') as fid:
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
    
    helper = Helper(ENGINE)
    capbuilder = CapBuilder(settings, helper)
    webconnector = connectors.WebConnector(settings, helper, capbuilder)
    wallbuilder = walls.WallBuilder(settings, helper, capbuilder, connector=webconnector)

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
            settings[item] = settings["oled_configurations"][settings["oled_mount_type"]][item]

    if settings["nrows"] > 5:
        column_style = settings["column_style_gt5"]

    settings["centerrow"] = settings["nrows"] - settings["centerrow_offset"]

    settings["lastrow"] = settings["nrows"] - 1
    settings["cornerrow"] = settings["lastrow"] - 1
    settings["lastcol"] = settings["ncols"] - 1

    oled_row = settings["nrows"] - 1
    plate_file = None

    # Derived values
    if settings["plate_style"] in ['NUB', 'HS_NUB']:
        settings["keyswitch_height"] = settings["nub_keyswitch_height"]
        settings["keyswitch_width"] = settings["nub_keyswitch_width"]
    elif settings["plate_style"] in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH']:
        settings["keyswitch_height"] = settings["undercut_keyswitch_height"]
        settings["keyswitch_width"] = settings["undercut_keyswitch_width"]
    else:
        settings["keyswitch_height"] = settings["hole_keyswitch_height"]
        settings["keyswitch_width"] = settings["hole_keyswitch_width"]

    if "AMOEBA" in settings["plate_style"]:
        settings["symmetry"] = "asymmetric"
        settings["plate_file"] = path.join(parts_path, r"amoeba_key_hole")
    elif 'HS_' in settings["plate_style"]:
        settings["symmetry"] = "asymmetric"
        pname = r"hot_swap_plate"
        if settings["plate_file_name"] is not None:
            pname = settings["plate_file_name"]
        settings["plate_file"] = path.join(parts_path, pname)
        # plate_offset = 0.0 # this overwrote the config variable

    if (settings["trackball_in_wall"] or ('TRACKBALL' in settings["thumb_style"])) and not settings["ball_side"] == 'both':
        settings["symmetry"] = "asymmetric"

    settings["mount_width"] = settings["keyswitch_width"] + 2 * settings["plate_rim"]
    settings["mount_height"] = settings["keyswitch_height"] + 2 * settings["plate_rim"]
    settings["mount_thickness"] = settings["plate_thickness"]

    if settings["default_1U_cluster"] and settings["thumb_style"] == 'DEFAULT':
        settings["double_plate_height"] = (.7 * settings["sa_double_length"] - settings["mount_height"]) / 3
        # double_plate_height = (.95 * sa_double_length - mount_height) / 3
    elif settings["thumb_style"] == 'DEFAULT':
        settings["double_plate_height"] = (.90 * settings["sa_double_length"] - settings["mount_height"]) / 3
    else:
        settings["double_plate_height"] = (settings["sa_double_length"] - settings["mount_height"]) / 3

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

    settings["cap_top_height"] = settings["plate_thickness"] + settings["sa_profile_key_height"]
    settings["row_radius"] = ((settings["mount_height"] + settings["extra_height"]) / 2) / (np.sin(settings["alpha"] / 2)) + settings["cap_top_height"]
    settings["column_radius"] = (
                            ((settings["mount_width"] + settings["extra_width"]) / 2) / (np.sin(settings["beta"] / 2))
                    ) + settings["cap_top_height"]
    settings["column_x_delta"] = -1 - settings["column_radius"] * np.sin(settings["beta"])
    settings["column_base_angle"] = settings["beta"] * (settings["centercol"] - 2)


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
    rj9_start = list(
        np.array([0, -3, 0])
        + np.array(
            capbuilder.key_position(
                list(np.array(wallbuilder.wall_locate3(0, 1)) + np.array([0, (settings["mount_height"] / 2), 0])),
                0,
                0,
            )
        )
    )

    rj9_position = (rj9_start[0], rj9_start[1], 11)


    def rj9_cube():
        logger.debug('rj9_cube()')
        shape = helper.box(14.78, 13, 22.38)

        return shape


    def rj9_space():
        logger.debug('rj9_space()')
        return helper.translate(rj9_cube(), rj9_position)


    def rj9_holder():
        logger.debug('rj9_holder()')
        shape = helper.union([helper.translate(helper.box(10.78, 9, 18.38), (0, 2, 0)), helper.translate(helper.box(10.78, 13, 5), (0, 0, 5))])
        shape = helper.difference(rj9_cube(), [shape])
        shape = helper.translate(shape, rj9_position)

        return shape


    usb_holder_position = capbuilder.key_position(
        list(np.array(wallbuilder.wall_locate2(0, 1)) + np.array([0, (settings["mount_height"] / 2), 0])), 1, 0
    )
    usb_holder_size = [6.5, 10.0, 13.6]
    usb_holder_thickness = 4


    def usb_holder():
        logger.debug('usb_holder()')
        shape = helper.box(
            usb_holder_size[0] + usb_holder_thickness,
            usb_holder_size[1],
            usb_holder_size[2] + usb_holder_thickness,
        )
        shape = helper.translate(shape,
                          (
                              usb_holder_position[0],
                              usb_holder_position[1],
                              (usb_holder_size[2] + usb_holder_thickness) / 2,
                          )
                          )
        return shape


    def usb_holder_hole():
        logger.debug('usb_holder_hole()')
        shape = helper.box(*usb_holder_size)
        shape = helper.translate(shape,
                          (
                              usb_holder_position[0],
                              usb_holder_position[1],
                              (usb_holder_size[2] + usb_holder_thickness) / 2,
                          )
                          )
        return shape


    def trrs_mount_point():
        shape = helper.box(6.2, 14, 5.2)
        jack = helper.translate(helper.rotate(helper.cylinder(2.6, 5), (90, 0, 0)), (0, 9, 0))
        jack_entry = helper.translate(helper.rotate(helper.cylinder(4, 5), (90, 0, 0)), (0, 11, 0))
        shape = helper.rotate(helper.translate(helper.union([shape, jack, jack_entry]), (0, 0, 10)), (0, 0, 75))

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
        shape = helper.translate(shape,
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
        ec11_mount = helper.import_file(path.join(parts_path, "ec11_mount_2"))
        ec11_mount = helper.translate(helper.rotate(ec11_mount, rot), pos)
        encoder_cut = helper.box(10.5, 10.5, 20)
        encoder_cut = helper.translate(helper.rotate(encoder_cut, rot), pos)
        shape = helper.difference(shape, [encoder_cut])
        shape = helper.union([shape, ec11_mount])
        # encoder_mount = translate(rotate(encoder_mount, (0, 0, 20)), (-27, -4, -15))
        return shape

    def usb_c_shape(width, height, depth):
        shape = helper.box(width, depth, height)
        cyl1 = helper.translate(helper.rotate(helper.cylinder(height / 2, depth), (90, 0, 0)), (width / 2, 0, 0))
        cyl2 = helper.translate(helper.rotate(helper.cylinder(height / 2, depth), (90, 0, 0)), (-width / 2, 0, 0))
        return helper.union([shape, cyl1, cyl2])

    def usb_c_hole():
        logger.debug('usb_c_hole()')
        return usb_c_shape(settings["usb_c_width"], settings["usb_c_height"], 20)

    def usb_c_mount_point():
        width = settings["usb_c_width"] * 1.2
        height = settings["usb_c_height"] * 1.2
        front_bit = helper.translate(usb_c_shape(settings["usb_c_width"] + 2, settings["usb_c_height"] + 2, settings["wall_thickness"] / 2), (0, (settings["wall_thickness"] / 2) + 1, 0))
        shape = helper.union([front_bit, usb_c_hole()])
        shape = helper.translate(shape,
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
            capbuilder.key_position(
                list(np.array(wallbuilder.wall_locate3(0, 1)) + np.array([0, (settings["mount_height"] / 2), 0])),
                0,
                0,
            )
        )
    )

    def blackpill_mount_hole():
        logger.debug('blackpill_external_mount_hole()')
        shape = helper.box(settings["blackpill_holder_width"], 20.0, settings["external_holder_height"] + .1)
        undercut = helper.box(settings["blackpill_holder_width"] + 8, 10.0, settings["external_holder_height"] + 8 + .1)
        shape = helper.union([shape, helper.translate(undercut, (0, -5, 0))])

        shape = helper.translate(shape,
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

        logo = helper.import_file(settings["logo_file"])
        logo = helper.rotate(logo, (90, 0, 180))
        logo = helper.translate(logo, offset)
        return logo

    def external_mount_hole():
        logger.debug('external_mount_hole()')
        shape = helper.box(settings["external_holder_width"], 20.0, settings["external_holder_height"] + .1)
        undercut = helper.box(settings["external_holder_width"] + 8, 10.0, settings["external_holder_height"] + 8 + .1)
        shape = helper.union([shape, helper.translate(undercut, (0, -5, 0))])

        shape = helper.translate(shape,
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
        shape = helper.cylinder(settings["trackball_hole_diameter"] / 2, settings["trackball_hole_height"])
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

        shape = helper.import_file(tb_file)
        sensor = helper.import_file(sens_file)
        cutter = helper.import_file(tbcut_file)
        if not btus:
            cutter = helper.union([cutter, helper.import_file(senscut_file)])

        # return shape, cutter
        return shape, cutter, sensor


    def trackball_ball(segments=100, side="right"):
        shape = helper.sphere(settings["ball_diameter"] / 2)
        return shape

    def generate_trackball(pos, rot, cluster):
        tb_t_offset = settings["tb_socket_translation_offset"]
        tb_r_offset = settings["tb_socket_rotation_offset"]

        if use_btus(cluster):
            tb_t_offset = settings["tb_btu_socket_translation_offset"]
            tb_r_offset = settings["tb_btu_socket_rotation_offset"]

        precut = trackball_cutout()
        precut = helper.rotate(precut, tb_r_offset)
        precut = helper.translate(precut, tb_t_offset)
        precut = helper.rotate(precut, rot)
        precut = helper.translate(precut, pos)

        shape, cutout, sensor = trackball_socket(btus=use_btus(cluster))

        shape = helper.rotate(shape, tb_r_offset)
        shape = helper.translate(shape, tb_t_offset)
        shape = helper.rotate(shape, rot)
        shape = helper.translate(shape, pos)

        if cluster is not None and settings["resin"] is False:
            shape = cluster.get_extras(shape, pos)

        cutout = helper.rotate(cutout, tb_r_offset)
        cutout = helper.translate(cutout, tb_t_offset)
        # cutout = rotate(cutout, tb_sensor_translation_offset)
        # cutout = translate(cutout, tb_sensor_rotation_offset)
        cutout = helper.rotate(cutout, rot)
        cutout = helper.translate(cutout, pos)

        # Small adjustment due to line to line surface / minute numerical error issues
        # Creates small overlap to assist engines in union function later
        sensor = helper.rotate(sensor, tb_r_offset)
        sensor = helper.translate(sensor, tb_t_offset)

        # Hackish?  Oh, yes. But it builds with latest cadquery.
        if ENGINE == 'cadquery':
            sensor = helper.translate(sensor, (0, 0, -15))
        # sensor = rotate(sensor, tb_sensor_translation_offset)
        # sensor = translate(sensor, tb_sensor_rotation_offset)
        sensor = helper.translate(sensor, (0, 0, .005))
        sensor = helper.rotate(sensor, rot)
        sensor = helper.translate(sensor, pos)

        ball = trackball_ball()
        ball = helper.rotate(ball, tb_r_offset)
        ball = helper.translate(ball, tb_t_offset)
        ball = helper.rotate(ball, rot)
        ball = helper.translate(ball, pos)

        # return precut, shape, cutout, ball
        return precut, shape, cutout, sensor, ball


    def generate_trackball_in_cluster(cluster):
        pos, rot = tbiw_position_rotation()
        if cluster.is_tb:
            pos, rot = cluster.position_rotation()
        return generate_trackball(pos, rot, cluster)


    def tbiw_position_rotation():
        base_pt1 = capbuilder.key_position(
            list(np.array([-settings["mount_width"] / 2, 0, 0]) + np.array([0, (settings["mount_height"] / 2), 0])),
            0, settings["cornerrow"] - settings["tbiw_ball_center_row"] - 1
        )
        base_pt2 = capbuilder.key_position(
            list(np.array([-settings["mount_width"] / 2, 0, 0]) + np.array([0, (settings["mount_height"] / 2), 0])),
            0, settings["cornerrow"] - settings["tbiw_ball_center_row"] + 1
        )
        base_pt0 = capbuilder.key_position(
            list(np.array([-settings["mount_width"] / 2, 0, 0]) + np.array([0, (settings["mount_height"] / 2), 0])),
            0, settings["cornerrow"] - settings["tbiw_ball_center_row"]
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
        wall_x_offsets = wallbuilder.get_left_wall_offsets(side)
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
            base_pt1 = capbuilder.key_position(
                list(np.array([-settings["mount_width"] / 2, 0, 0]) + np.array([0, (settings["mount_height"] / 2), 0])), 0, _oled_center_row - 1
            )
            base_pt2 = capbuilder.key_position(
                list(np.array([-settings["mount_width"] / 2, 0, 0]) + np.array([0, (settings["mount_height"] / 2), 0])), 0, _oled_center_row + 1
            )
            base_pt0 = capbuilder.key_position(
                list(np.array([-settings["mount_width"] / 2, 0, 0]) + np.array([0, (settings["mount_height"] / 2), 0])), 0, _oled_center_row
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

        hole = helper.box(mount_ext_width, mount_ext_up_height, settings["oled_mount_cut_depth"] + .01)
        hole = helper.translate(hole, (0., top_hole_start + top_hole_length / 2, 0.))

        hole_down = helper.box(mount_ext_width, mount_ext_height, settings["oled_mount_depth"] + settings["oled_mount_cut_depth"] / 2)
        hole_down = helper.translate(hole_down, (0., 0., -settings["oled_mount_cut_depth"] / 4))
        hole = helper.union([hole, hole_down])

        shape = helper.box(mount_ext_width, mount_ext_height, settings["oled_mount_depth"])

        conn_hole_start = (-mount_ext_height / 2.0 + settings["oled_mount_rim"]) - 2
        conn_hole_length = (
                settings["oled_edge_overlap_end"] + settings["oled_edge_overlap_connector"]
                + settings["oled_edge_overlap_clearance"] + settings["oled_thickness"]
        ) + 4
        conn_hole = helper.box(settings["oled_mount_width"], conn_hole_length + .01, settings["oled_mount_depth"])
        conn_hole = helper.translate(conn_hole, (
            0,
            conn_hole_start + conn_hole_length / 2,
            -settings["oled_edge_overlap_thickness"]
        ))

        end_hole_length = (
                settings["oled_edge_overlap_end"] + settings["oled_edge_overlap_clearance"]
        )
        end_hole_start = mount_ext_height / 2.0 - settings["oled_mount_rim"] - end_hole_length
        end_hole = helper.box(settings["oled_mount_width"], end_hole_length + .01, settings["oled_mount_depth"])
        end_hole = helper.translate(end_hole, (
            0,
            end_hole_start + end_hole_length / 2,
            -settings["oled_edge_overlap_thickness"]
        ))

        top_hole_start = -mount_ext_height / 2.0 + settings["oled_mount_rim"] + settings["oled_edge_overlap_end"] + settings["oled_edge_overlap_connector"]
        top_hole_length = settings["oled_mount_height"]
        top_hole = helper.box(settings["oled_mount_width"], top_hole_length, settings["oled_edge_overlap_thickness"] + settings["oled_thickness"] - settings["oled_edge_chamfer"])
        top_hole = helper.translate(top_hole, (
            0,
            top_hole_start + top_hole_length / 2,
            (settings["oled_mount_depth"] - settings["oled_edge_overlap_thickness"] - settings["oled_thickness"] - settings["oled_edge_chamfer"]) / 2.0
        ))

        top_chamfer_1 = helper.box(
            settings["oled_mount_width"],
            top_hole_length,
            0.01
        )
        top_chamfer_2 = helper.box(
            settings["oled_mount_width"] + 2 * settings["oled_edge_chamfer"],
            top_hole_length + 2 * settings["oled_edge_chamfer"],
            0.01
        )
        top_chamfer_1 = helper.translate(top_chamfer_1, (0, 0, -settings["oled_edge_chamfer"] - .05))

        top_chamfer_1 = helper.hull_from_shapes([top_chamfer_1, top_chamfer_2])

        top_chamfer_1 = helper.translate(top_chamfer_1, (
            0,
            top_hole_start + top_hole_length / 2,
            settings["oled_mount_depth"] / 2.0 + .05
        ))

        top_hole = helper.union([top_hole, top_chamfer_1])

        shape = helper.difference(shape, [conn_hole, top_hole, end_hole])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = helper.rotate(shape, oled_mount_rotation_xyz)
        shape = helper.translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = helper.rotate(hole, oled_mount_rotation_xyz)
        hole = helper.translate(hole,
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
        hole = helper.box(mount_ext_width, mount_ext_height, settings["oled_mount_cut_depth"] + .01)

        shape = helper.box(mount_ext_width, mount_ext_height, settings["oled_mount_depth"])
        shape = helper.difference(shape, [helper.box(settings["oled_mount_width"], settings["oled_mount_height"], settings["oled_mount_depth"] + .1)])

        clip_slot = helper.box(
            settings["oled_clip_width"] + 2 * settings["oled_clip_width_clearance"],
            settings["oled_mount_height"] + 2 * settings["oled_clip_thickness"] + 2 * settings["oled_clip_overhang"],
            settings["oled_mount_depth"] + .1
        )

        shape = helper.difference(shape, [clip_slot])

        clip_undercut = helper.box(
            settings["oled_clip_width"] + 2 * settings["oled_clip_width_clearance"],
            settings["oled_mount_height"] + 2 * settings["oled_clip_thickness"] + 2 * settings["oled_clip_overhang"] + 2 * settings["oled_clip_undercut"],
            settings["oled_mount_depth"] + .1
        )

        clip_undercut = helper.translate(clip_undercut, (0., 0., settings["oled_clip_undercut_thickness"]))
        shape = helper.difference(shape, [clip_undercut])

        plate = helper.box(
            settings["oled_mount_width"] + .1,
            settings["oled_mount_height"] - 2 * settings["oled_mount_connector_hole"],
            settings["oled_mount_depth"] - settings["oled_thickness"]
        )
        plate = helper.translate(plate, (0., 0., -settings["oled_thickness"] / 2.0))
        shape = helper.union([shape, plate])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = helper.rotate(shape, oled_mount_rotation_xyz)
        shape = helper.translate(shape,
                          (
                              oled_mount_location_xyz[0],
                              oled_mount_location_xyz[1],
                              oled_mount_location_xyz[2],
                          )
                          )

        hole = helper.rotate(hole, oled_mount_rotation_xyz)
        hole = helper.translate(hole,
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

        shape = helper.box(mount_ext_width - .1, mount_ext_height - .1, settings["oled_mount_bezel_thickness"])
        shape = helper.translate(shape, (0., 0., settings["oled_mount_bezel_thickness"] / 2.))

        hole_1 = helper.box(
            settings["oled_screen_width"] + 2 * settings["oled_mount_bezel_chamfer"],
            settings["oled_screen_length"] + 2 * settings["oled_mount_bezel_chamfer"],
            .01
        )
        hole_2 = helper.box(settings["oled_screen_width"], settings["oled_screen_length"], 2.05 * settings["oled_mount_bezel_thickness"])
        hole = helper.hull_from_shapes([hole_1, hole_2])

        shape = helper.difference(shape, [helper.translate(hole, (0., 0., settings["oled_mount_bezel_thickness"]))])

        clip_leg = helper.box(settings["oled_clip_width"], settings["oled_clip_thickness"], oled_leg_depth)
        clip_leg = helper.translate(clip_leg, (
            0.,
            0.,
            # (oled_mount_height+2*oled_clip_overhang+oled_clip_thickness)/2,
            -oled_leg_depth / 2.
        ))

        latch_1 = helper.box(
            settings["oled_clip_width"],
            settings["oled_clip_overhang"] + settings["oled_clip_thickness"],
            .01
        )
        latch_2 = helper.box(
            settings["oled_clip_width"],
            settings["oled_clip_thickness"] / 2,
            settings["oled_clip_extension"]
        )
        latch_2 = helper.translate(latch_2, (
            0.,
            -(-settings["oled_clip_thickness"] / 2 + settings["oled_clip_thickness"] + settings["oled_clip_overhang"]) / 2,
            -settings["oled_clip_extension"] / 2
        ))
        latch = helper.hull_from_shapes([latch_1, latch_2])
        latch = helper.translate(latch, (
            0.,
            settings["oled_clip_overhang"] / 2,
            -oled_leg_depth
        ))

        clip_leg = helper.union([clip_leg, latch])

        clip_leg = helper.translate(clip_leg, (
            0.,
            (settings["oled_mount_height"] + 2 * settings["oled_clip_overhang"] + settings["oled_clip_thickness"]) / 2 - settings["oled_clip_y_gap"],
            0.
        ))

        shape = helper.union([shape, clip_leg, helper.mirror(clip_leg, 'XZ')])

        return shape


    def oled_undercut_mount_frame(side='right'):
        mount_ext_width = settings["oled_mount_width"] + 2 * settings["oled_mount_rim"]
        mount_ext_height = settings["oled_mount_height"] + 2 * settings["oled_mount_rim"]
        hole = helper.box(mount_ext_width, mount_ext_height, settings["oled_mount_cut_depth"] + .01)

        shape = helper.box(mount_ext_width, mount_ext_height, settings["oled_mount_depth"])
        shape = helper.difference(shape, [helper.box(settings["oled_mount_width"], settings["oled_mount_height"], settings["oled_mount_depth"] + .1)])
        undercut = helper.box(
            settings["oled_mount_width"] + 2 * settings["oled_mount_undercut"],
            settings["oled_mount_height"] + 2 * settings["oled_mount_undercut"],
            settings["oled_mount_depth"])
        undercut = helper.translate(undercut, (0., 0., -settings["oled_mount_undercut_thickness"]))
        shape = helper.difference(shape, [undercut])

        oled_mount_location_xyz, oled_mount_rotation_xyz = oled_position_rotation(side=side)

        shape = helper.rotate(shape, oled_mount_rotation_xyz)
        shape = helper.translate(shape, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                          )

        hole = helper.rotate(hole, oled_mount_rotation_xyz)
        hole = helper.translate(hole, (
            oled_mount_location_xyz[0],
            oled_mount_location_xyz[1],
            oled_mount_location_xyz[2],
        )
                         )

        return hole, shape


    def teensy_holder():
        logger.debug('teensy_holder()')
        teensy_width = 20
        teensy_height = 12
        teensy_length = 33
        teensy2_length = 53
        teensy_pcb_thickness = 2
        teensy_offset_height = 5
        teensy_holder_top_length = 18
        teensy_holder_width = 7 + teensy_pcb_thickness
        teensy_holder_height = 6 + teensy_width
        teensy_top_xy = capbuilder.key_position(wallbuilder.wall_locate3(-1, 0), 0, settings["centerrow"] - 1)
        teensy_bot_xy = capbuilder.key_position(wallbuilder.wall_locate3(-1, 0), 0, settings["centerrow"] + 1)
        teensy_holder_length = teensy_top_xy[1] - teensy_bot_xy[1]
        teensy_holder_offset = -teensy_holder_length / 2
        teensy_holder_top_offset = (teensy_holder_top_length / 2) - teensy_holder_length

        s1 = helper.box(3, teensy_holder_length, 6 + teensy_width)
        s1 = helper.translate(s1, [1.5, teensy_holder_offset, 0])

        s2 = helper.box(teensy_pcb_thickness, teensy_holder_length, 3)
        s2 = helper.translate(s2,
                       (
                           (teensy_pcb_thickness / 2) + 3,
                           teensy_holder_offset,
                           -1.5 - (teensy_width / 2),
                       )
                       )

        s3 = helper.box(teensy_pcb_thickness, teensy_holder_top_length, 3)
        s3 = helper.translate(s3,
                       [
                           (teensy_pcb_thickness / 2) + 3,
                           teensy_holder_top_offset,
                           1.5 + (teensy_width / 2),
                       ]
                       )

        s4 = helper.box(4, teensy_holder_top_length, 4)
        s4 = helper.translate(s4,
                       [teensy_pcb_thickness + 5, teensy_holder_top_offset, 1 + (teensy_width / 2)]
                       )

        shape = helper.union((s1, s2, s3, s4))

        shape = helper.translate(shape, [-teensy_holder_width, 0, 0])
        shape = helper.translate(shape, [-1.4, 0, 0])
        shape = helper.translate(shape,
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
            new_cyl = helper.translate(helper.cylinder(radius, height), (0, 0, offset))
            if cyl is None:
                cyl = new_cyl
            else:
                cyl = helper.union([cyl, new_cyl])
            offset -= height / 2
        cyl = helper.translate(helper.rotate(cyl, (0, 180, 0)), (0, 0, -0.01))
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
                shape = helper.translate(helper.cylinder(radius=bottom_radius, height=new_height),
                                 (0, 0, mag_offset - (new_height / 2))  # offset magnet by 1 mm in case
                                 )
            else:
                shape = helper.translate(helper.cone(r1=bottom_radius, r2=top_radius, height=new_height), (0, 0, -new_height / 2))

        if settings["magnet_bottom"]:
            if not hole:
                shape = helper.union((
                    shape,
                    helper.translate(helper.sphere(top_radius), (0, 0, mag_offset / 2)),
                ))
        else:
            shape = helper.union((
                shape,
                helper.translate(helper.sphere(top_radius), (0, 0,  (new_height / 2))),
            ))
        return shape

    def screw_insert(column, row, bottom_radius, top_radius, height, side='right', hole=False):
        logger.debug('screw_insert()')
        position = screw_position(column, row, side)
        shape = screw_insert_shape(bottom_radius, top_radius, height, hole=hole)
        shape = helper.translate(shape, [position[0], position[1], height / 2])

        return shape

    def screw_position(column, row,  side='right'):
        logger.debug('screw_position()')
        shift_right = column == settings["lastcol"]
        shift_left = column == 0
        shift_up = (not (shift_right or shift_left)) and (row == 0)
        shift_down = (not (shift_right or shift_left)) and (row >= settings["lastrow"])

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
            position = capbuilder.key_position(
                list(np.array(wallbuilder.wall_locate2(0, 1)) + np.array([0, (settings["mount_height"] / 2) + shift_up_adjust, 0])),
                column,
                row,
            )
        elif shift_down:
            position = capbuilder.key_position(
                list(np.array(wallbuilder.wall_locate2(0, -1)) - np.array([0, (settings["mount_height"] / 2) + shift_down_adjust, 0])),
                column,
                row,
            )
        elif shift_left:
            position = list(
                np.array(capbuilder.left_key_position(row, 0, side=side)) + np.array(wallbuilder.wall_locate3(-1, 0)) + np.array(
                    (shift_left_adjust, 0, 0))
            )
        else:
            position = capbuilder.key_position(
                list(np.array(wallbuilder.wall_locate2(1, 0)) + np.array([(settings["mount_height"] / 2), 0, 0]) + np.array(
                    (shift_right_adjust, 0, 0))
                     ),
                column,
                row,
            )

        return position

    def screw_insert_thumb(bottom_radius, top_radius, top_height, hole=False, side="right"):
        position = cluster(side).screw_positions()
        shape = screw_insert_shape(bottom_radius, top_radius, top_height, hole=hole)
        shape = helper.translate(shape, [position[0], position[1], top_height / 2])
        return shape


    def screw_insert_all_shapes(bottom_radius, top_radius, height, offset=0, side='right', hole=False):
        logger.debug('screw_insert_all_shapes()')
        so = settings["screw_offsets"]
        shape = (
            helper.translate(screw_insert(0, 0, bottom_radius, top_radius, height, side=side, hole=hole), (so[0][0], so[0][1], so[0][2] + offset)),  # rear left
            helper.translate(screw_insert(0, settings["lastrow"] - 1, bottom_radius, top_radius, height, side=side, hole=hole), (so[1][0], so[1][1] + settings["left_wall_lower_y_offset"], so[1][2] + offset)),  # front left
            helper.translate(screw_insert(3, settings["lastrow"], bottom_radius, top_radius, height, side=side, hole=hole), (so[2][0], so[2][1], so[2][2] + offset)),  # front middle
            helper.translate(screw_insert(3, 0, bottom_radius, top_radius, height, side=side, hole=hole), (so[3][0], so[3][1], so[3][2] + offset)),  # rear middle
            helper.translate(screw_insert(settings["lastcol"], 0, bottom_radius, top_radius, height, side=side, hole=hole), (so[4][0], so[4][1], so[4][2] + offset)),  # rear right
            helper.translate(screw_insert(settings["lastcol"], settings["lastrow"] - 1, bottom_radius, top_radius, height, side=side, hole=hole), (so[5][0], so[5][1], so[5][2] + offset)),  # front right
            helper.translate(screw_insert_thumb(bottom_radius, top_radius, height, side=side, hole=hole), (so[6][0], so[6][1], so[6][2] + offset)),  # thumb cluster
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
        s1 = helper.box(
            settings["wire_post_diameter"], settings["wire_post_diameter"], settings["wire_post_height"]
        )
        s1 = helper.translate(s1, [0, -settings["wire_post_diameter"] * 0.5 * direction, 0])

        s2 = helper.box(
            settings["wire_post_diameter"], settings["wire_post_overhang"], settings["wire_post_diameter"]
        )
        s2 = helper.translate(s2,
                       [0, -settings["wire_post_overhang"] * 0.5 * direction, -settings["wire_post_height"] / 2]
                       )

        shape = helper.union((s1, s2))
        shape = helper.translate(shape, [0, -offset, (-settings["wire_post_height"] / 2) + 3])
        shape = helper.rotate(shape, [-settings["alpha"] / 2, 0, 0])
        shape = helper.translate(shape, (3, -settings["mount_height"] / 2, 0))

        return shape

    def model_side(side="right"):
        logger.debug('model_side()' + side)
        shape = helper.union([capbuilder.key_holes(side=side)])
        if debug_exports:
            helper.export_file(shape=shape, fname=path.join(r".", "things", r"debug_key_plates"))
        connector_shape = webconnector.connectors()
        shape = helper.union([shape, connector_shape])
        if debug_exports:
            helper.export_file(shape=shape, fname=path.join(r".", "things", r"debug_connector_shape"))
        thumb_shape = cluster(side).thumb(side=side)
        if debug_exports:
            helper.export_file(shape=thumb_shape, fname=path.join(r".", "things", r"debug_thumb_shape"))
        shape = helper.union([shape, thumb_shape])
        thumb_connector_shape = cluster(side).thumb_connectors(side=side)
        shape = helper.union([shape, thumb_connector_shape])
        if debug_exports:
            helper.export_file(shape=shape, fname=path.join(r".", "things", r"debug_thumb_connector_shape"))
        walls_shape = wallbuilder.case_walls(cluster(side=side), side=side)
        if debug_exports:
            helper.export_file(shape=walls_shape, fname=path.join(r".", "things", r"debug_walls_shape"))
        s2 = helper.union([walls_shape])
        s2 = helper.union([s2, *screw_insert_outers(side=side)])

        if settings["trrs_hole"]:
            s2 = helper.difference(s2, [trrs_mount_point()])

        if is_side(side, settings["controller_side"]):
            if settings["controller_mount_type"] in ['RJ9_USB_TEENSY', 'USB_TEENSY']:
                s2 = helper.union([s2, teensy_holder()])

            if settings["controller_mount_type"] in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL', 'USB_WALL', 'USB_TEENSY']:
                s2 = helper.union([s2, usb_holder()])
                s2 = helper.difference(s2, [usb_holder_hole()])

            if settings["controller_mount_type"] in ['USB_C_WALL']:
                s2 = helper.difference(s2, [usb_c_mount_point()])

            if settings["controller_mount_type"] in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
                s2 = helper.difference(s2, [rj9_space()])

            if settings["controller_mount_type"] in ['BLACKPILL_EXTERNAL']:
                s2 = helper.difference(s2, [blackpill_mount_hole()])

            if settings["controller_mount_type"] in ['EXTERNAL']:
                s2 = helper.difference(s2, [external_mount_hole()])

            if settings["controller_mount_type"] in ['None']:
                pass  # do nothing, only here to expressly state inaction.

        s2 = helper.difference(s2, [helper.union(screw_insert_holes(side=side))])

        if side == "right" and settings["logo_file"] not in ["", None]:
            s2 = helper.union([s2, get_logo()])

        shape = helper.union([shape, s2])

        if settings["controller_mount_type"] in ['RJ9_USB_TEENSY', 'RJ9_USB_WALL']:
            shape = helper.union([shape, rj9_holder()])

        if is_oled(side):
            if settings["oled_mount_type"] == "UNDERCUT":
                hole, frame = oled_undercut_mount_frame(side=side)
                shape = helper.difference(shape, [hole])
                shape = helper.union([shape, frame])

            elif settings["oled_mount_type"] == "SLIDING":
                hole, frame = oled_sliding_mount_frame(side=side)
                shape = helper.difference(shape, [hole])
                shape = helper.union([shape, frame])
                if settings["encoder_in_wall"]:
                    shape = encoder_wall_mount(shape, side)

            elif settings["oled_mount_type"] == "CLIP":
                hole, frame = oled_clip_mount_frame(side=side)
                shape = helper.difference(shape, [hole])
                shape = helper.union([shape, frame])

        if not quickly:
            if settings["trackball_in_wall"] and is_side(side, settings["ball_side"]):
                tbprecut, tb, tbcutout, sensor, ball = generate_trackball_in_wall()

                shape = helper.difference(shape, [tbprecut])
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
                shape = helper.union([shape, tb])
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
                shape = helper.difference(shape, [tbcutout])
                # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
                # export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
                shape = helper.union([shape, sensor])

                if settings["show_caps"]:
                    shape = helper.add([shape, ball])

            elif cluster(side).is_tb:
                tbprecut, tb, tbcutout, sensor, ball = generate_trackball_in_cluster(cluster(side))

                shape = helper.difference(shape, [tbprecut])
                if cluster(side).has_btus():
                    shape = helper.difference(shape, [tbcutout])
                    shape = helper.union([shape, tb])
                else:
                    # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_1"))
                    shape = helper.union([shape, tb])
                    # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_2"))
                    shape = helper.difference(shape, [tbcutout])
                    # export_file(shape=shape, fname=path.join(save_path, config_name + r"_test_3a"))
                    # export_file(shape=add([shape, sensor]), fname=path.join(save_path, config_name + r"_test_3b"))
                    shape = helper.union([shape, sensor])

                if settings["show_caps"]:
                    shape = helper.add([shape, ball])

        block = helper.translate(helper.box(400, 400, 40), (0, 0, -20))
        shape = helper.difference(shape, [block])

        if settings["show_caps"]:
            shape = helper.add([shape, cluster(side).thumbcaps(side=side)])
            shape = helper.add([shape, capbuilder.caps()])

        if side == "left":
            shape = helper.mirror(shape, 'YZ')

        return shape, walls_shape

    def wrist_rest(base, plate, side="right"):
        rest = helper.import_file(path.join(parts_path, "dactyl_wrist_rest_v3_" + side))
        rest = helper.rotate(rest, (0, 0, -60))
        rest = helper.translate(rest, (30, -150, 26))
        rest = helper.union([rest, helper.translate(base, (0, 0, 5)), plate])
        return rest

    # NEEDS TO BE SPECIAL FOR CADQUERY
    def baseplate(shape, wedge_angle=None, side='right'):
        global logo_file
        if ENGINE == 'cadquery':
            # shape = mod_r
            shape = helper.union([shape, *screw_insert_outers(side=side)])
            # tool = translate(screw_insert_screw_holes(side=side), [0, 0, -10])
            if settings["magnet_bottom"]:
                tool = screw_insert_all_shapes(settings["screw_hole_diameter"] / 2., settings["screw_hole_diameter"] / 2., 2.1, side=side)
                for item in tool:
                    item = helper.translate(item, [0, 0, 1.2])
                    shape = helper.difference(shape, [item])
            else:
                tool = screw_insert_all_shapes(settings["screw_hole_diameter"] / 2., settings["screw_hole_diameter"] / 2., 350, side=side)
                for item in tool:
                    item = helper.translate(item, [0, 0, -10])
                    shape = helper.difference(shape, [item])

            shape = helper.translate(shape, (0, 0, -0.0001))

            square = cq.Workplane('XY').rect(1000, 1000)
            for wire in square.wires().objects:
                plane = cq.Workplane('XY').add(cq.Face.makeFromWires(wire))
            shape = helper.intersect(shape, plane)

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
                inner_shape = helper.translate(inner_shape, (0, 0, -settings["base_rim_thickness"]))
                if settings["block_bottoms"]:
                    inner_shape = blockerize(inner_shape)
                if settings["logo_file"] not in ["", None]:
                    logo_offset = [
                        -10,
                        -10,
                        -0.5
                    ]
                    logo = helper.import_file(settings["logo_file"])
                    if side == "left":
                        logo = helper.mirror(logo, "YZ")
                    if settings["ncols"] <= 6:
                        logo_offset[0] -= 12 * (7 - settings["ncols"])
                    if settings["nrows"] <= 5:
                        logo_offset[1] += 15 * (6 - settings["ncols"])
                    logo = helper.translate(logo, logo_offset)

                    inner_shape = helper.union([inner_shape, logo])

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
                        helper.translate(
                            helper.cylinder(settings["screw_cbore_diameter"] / 2.0, settings["screw_cbore_depth"]),
                            (loc.x, loc.y, 0)
                            # (loc.x, loc.y, screw_cbore_depth/2)
                        )
                    )
                shape = helper.difference(shape, hole_shapes)
                shape = helper.translate(shape, (0, 0, -settings["base_rim_thickness"]))
                shape = helper.union([shape, inner_shape])
                if settings["magnet_bottom"]:
                    shape = helper.difference(shape, [helper.translate(magnet, (0, 0, 0.05 - (settings["screw_insert_height"] / 2))) for magnet in list(tool)])

            return shape
        else:

            shape = helper.union([
                wallbuilder.case_walls(cluster(side=side), side=side),
                *screw_insert_outers(side=side)
            ])

            tool = helper.translate(helper.union(screw_insert_screw_holes(side=side)), [0, 0, -10])
            base = helper.box(1000, 1000, .01)
            shape = shape - tool
            shape = helper.intersect(shape, base)

            shape = helper.translate(shape, [0, 0, -0.001])

            return sl.projection(cut=True)(shape)


    def run():
        mod_r, walls_r = model_side(side="right")
        if settings["resin"] and ENGINE == "cadquery":
            mod_r = helper.rotate(mod_r, (333.04, 43.67, 85.00))
        helper.export_file(shape=mod_r, fname=path.join(save_path, r_config_name + r"_right"))

        if settings["right_side_only"]:
            logger.warn(">>>>>  RIGHT SIDE ONLY: Only rendering a the right side.")
            return
        base = baseplate(walls_r, side='right')
        helper.export_file(shape=base, fname=path.join(save_path, r_config_name + r"_right_plate"))
        if quickly:
            logger.warn(">>>>>  QUICK RENDER: Only rendering a the right side and bottom plate.")
            return
        helper.export_dxf(shape=base, fname=path.join(save_path, r_config_name + r"_right_plate"))

        # rest = wrist_rest(mod_r, base, side="right")
        #
        # export_file(shape=rest, fname=path.join(save_path, config_name + r"_right_wrist_rest"))

        # if symmetry == "asymmetric":

        mod_l, walls_l = model_side(side="left")
        if settings["resin"] and ENGINE == "cadquery":
            mod_l = helper.rotate(mod_l, (333.04, 317.33, 286.35))
        helper.export_file(shape=mod_l, fname=path.join(save_path, l_config_name + r"_left"))

        base_l = helper.mirror(baseplate(walls_l, side='left'), 'YZ')
        helper.export_file(shape=base_l, fname=path.join(save_path, l_config_name + r"_left_plate"))
        helper.export_dxf(shape=base_l, fname=path.join(save_path, l_config_name + r"_left_plate"))

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
            settings["oled_mount_location_xyz"] = (0.0, 0.0, -settings["oled_mount_depth"] / 2)
            settings["oled_mount_rotation_xyz"] = (0.0, 0.0, 0.0)
            helper.export_file(shape=oled_clip(), fname=path.join(save_path, config_name + r"_oled_clip"))
            # export_file(shape=oled_clip_mount_frame()[1],
            #             fname=path.join(save_path, config_name + r"_oled_clip_test"))
            # export_file(shape=union((oled_clip_mount_frame()[1], oled_clip())),
            #             fname=path.join(save_path, config_name + r"_oled_clip_assy_test"))

    right_cluster = Cluster(settings, helper, wallbuilder, connector=webconnector)

    if right_cluster.is_tb:
        if settings["ball_side"] == "both":
            left_cluster = right_cluster
        elif settings["ball_side"] == "left":
            left_cluster = right_cluster
            right_cluster = Cluster(settings, helper, wallbuilder, other_thumb=True)
        else:
            left_cluster = Cluster(settings, helper, wallbuilder, other_thumb=True)
    elif settings["other_thumb"] != "DEFAULT" and settings["other_thumb"] != settings["thumb_style"]:
        left_cluster = Cluster(settings, helper, wallbuilder, other_thumb=True)
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

