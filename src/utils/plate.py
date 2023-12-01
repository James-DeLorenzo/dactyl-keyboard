import logging
import numpy as np

logger = logging.getLogger()

def single_plate(settings, helpers, cylinder_segments=100, side="right"):
    plate_style = settings['plate_style']
    if plate_style == "MXLEDBIT":
        pcb_width = 19
        pcb_length = 19
        pcb_height = 1.6

        degrees = np.degrees(settings["alpha"] / 2)
        frame = helpers.box(21, 21, 3)
        frame = helpers.difference(frame, [helpers.box(18.5, 18.5, 5)])
        frame = helpers.difference(frame, [helpers.box(19.5, 19.5, 2.5)])
        connector = helpers.translate(helpers.rotate(helpers.box(21, 4, 2.5), (degrees, 0, 0)), (0, 11.5, 0))
        frame = helpers.translate(helpers.union([frame, connector]), (0, 0, -5))
        return frame

    if plate_style in ['NUB', 'HS_NUB']:
        tb_border = (settings["mount_height"] - settings["keyswitch_height"]) / 2
        top_wall = helpers.box(settings["mount_width"], tb_border, settings["plate_thickness"])
        top_wall = helpers.translate(top_wall, (0, (tb_border / 2) + (settings["keyswitch_height"] / 2), settings["plate_thickness"] / 2))

        lr_border = (settings["mount_width"] - settings["keyswitch_width"]) / 2
        left_wall = helpers.box(lr_border, settings["mount_height"], settings["plate_thickness"])
        left_wall = helpers.translate(left_wall, ((lr_border / 2) + (settings["keyswitch_width"] / 2), 0, settings["plate_thickness"] / 2))

        side_nub = helpers.cylinder(radius=1, height=2.75)
        side_nub = helpers.rotate(side_nub, (90, 0, 0))
        side_nub = helpers.translate(side_nub, (settings["keyswitch_width"] / 2, 0, 1))

        nub_cube = helpers.box(1.5, 2.75, settings["plate_thickness"])
        nub_cube = helpers.translate(nub_cube, ((1.5 / 2) + (settings["keyswitch_width"] / 2), 0, settings["plate_thickness"] / 2))

        side_nub2 = helpers.tess_hull(shapes=(side_nub, nub_cube))
        side_nub2 = helpers.union([side_nub2, side_nub, nub_cube])

        plate_half1 = helpers.union([top_wall, left_wall, side_nub2])
        plate_half2 = plate_half1
        plate_half2 = helpers.mirror(plate_half2, 'XZ')
        plate_half2 = helpers.mirror(plate_half2, 'YZ')

        plate = helpers.union([plate_half1, plate_half2])

    # elif plate_style in "AMOEBA":  # 'HOLE' or default, square cutout for non-nub designs.
    #     plate = box(settings["mount_width"], mount_height, mount_thickness)
    #     plate = translate(plate, (0.0, 0.0, mount_thickness / 2.0))
    #
    #     shape_cut = box(keyswitch_width + 2, settings["keyswitch_height"] + 2, mount_thickness * 2 + .02)
    #     shape_cut = translate(shape_cut, (0.0, 0.0, mount_thickness - .01))
    #
    #     plate = difference(plate, [shape_cut])

    else:  # 'HOLE' or default, square cutout for non-nub designs.
        plate = helpers.box(settings["mount_width"], settings["mount_height"], settings["mount_thickness"])
        plate = helpers.translate(plate, (0.0, 0.0, settings["mount_thickness"] / 2.0))

        shape_cut = helpers.box(settings["keyswitch_width"], settings["keyswitch_height"], settings["mount_thickness"] * 2 + .02)
        shape_cut = helpers.translate(shape_cut, (0.0, 0.0, settings["mount_thickness"] - .01))

        plate = helpers.difference(plate, [shape_cut])

    if settings["plate_file"] is not None:
        socket = helpers.import_file(settings["plate_file"])
        socket = helpers.translate(socket, [0, 0, settings["plate_thickness"] + settings["plate_offset"]])
        plate = helpers.union([plate, socket])

    if plate_style in ['UNDERCUT', 'HS_UNDERCUT', 'NOTCH', 'HS_NOTCH', 'AMOEBA']:
        if plate_style in ['UNDERCUT', 'HS_UNDERCUT']:
            undercut = helpers.box(
                settings["keyswitch_width"] + 2 * settings["clip_undercut"],
                settings["keyswitch_height"] + 2 * settings["clip_undercut"],
                settings["mount_thickness"]
            )

        if plate_style in ['NOTCH', 'HS_NOTCH', 'AMOEBA']:
            undercut = helpers.box(
                settings["notch_width"],
                settings["keyswitch_height"] + 2 * settings["clip_undercut"],
                settings["mount_thickness"]
            )
            undercut = helpers.union([undercut,
                helpers.box(
                    settings["keyswitch_width"] + 2 * settings["clip_undercut"],
                    settings["notch_width"],
                    settings["mount_thickness"]
                )
            ])

        undercut = helpers.translate(settings["undercut"], (0.0, 0.0, -settings["clip_thickness"] + settings["mount_thickness"] / 2.0))

        if settings["ENGINE"] == 'cadquery' and settings["undercut_transition"] > 0:
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

############
## Thumbs ##
############


def adjustable_plate_size(settings, Usize=1.5):
    return (Usize * settings["sa_length"] - settings["mount_height"]) / 2


def adjustable_plate_half(settings, helper, Usize=1.5):
    logger.debug('double_plate()')
    adjustable_plate_height = adjustable_plate_size(Usize)
    top_plate = helper.box(settings["mount_width"], adjustable_plate_height, settings["web_thickness"])
    top_plate = helper.translate(top_plate,
                          [0, (adjustable_plate_height + settings["mount_height"]) / 2, settings["plate_thickness"] - (settings["web_thickness"] / 2)]
                          )
    return top_plate


def adjustable_plate(settings, helper, Usize=1.5):
    logger.debug('double_plate()')
    top_plate = adjustable_plate_half(settings, Usize)
    return helper.union((top_plate, helper.mirror(top_plate, 'XZ')))


def double_plate_half(settings, helper):
    logger.debug('double_plate()')
    top_plate = helper.box(settings["mount_width"], settings["double_plate_height"], settings["web_thickness"])
    top_plate = helper.translate(top_plate,
                          [0, (settings["double_plate_height"] + settings["mount_height"]) / 2, settings["plate_thickness"] - (settings["web_thickness"] / 2)]
                          )
    return top_plate


def double_plate(settings, helper):
    logger.debug('double_plate()')
    top_plate = double_plate_half(settings, helper)
    return helper.union((top_plate, helper.mirror(top_plate, 'XZ')))


