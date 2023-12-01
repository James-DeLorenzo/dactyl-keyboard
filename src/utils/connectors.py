import logging
import numpy as np

logger = logging.getLogger()

####################
## Web Connectors ##
####################
class WebConnector():

    def __init__(self, settings, helper, capbuilder) -> None:
        self.settings = settings
        self.helper = helper
        self.caps = capbuilder

    def web_post(self, ):
        logger.debug('web_post()')
        post = self.helper.box(self.settings["post_size"], self.settings["post_size"], self.settings["web_thickness"])
        post = self.helper.translate(post, (0, 0, self.settings["plate_thickness"] - (self.settings["web_thickness"] / 2)))
        return post


    def web_post_tr(self,  off_w=0, off_h=0, off_z=0):
        return self.helper.translate(self.web_post(), ((self.settings["mount_width"] / 2.0) + off_w, (self.settings["mount_height"] / 2.0) + off_h, 0))


    def web_post_tl(self,  off_w=0, off_h=0, off_z=0):
        return self.helper.translate(self.web_post(), (-(self.settings["mount_width"] / 2.0) - off_w, (self.settings["mount_height"] / 2.0) + off_h, 0))


    def web_post_bl(self,  off_w=0, off_h=0, off_z=0):
        return self.helper.translate(self.web_post(), (-(self.settings["mount_width"] / 2.0) - off_w, -(self.settings["mount_height"] / 2.0) - off_h, 0))


    def web_post_br(self,  off_w=0, off_h=0, off_z=0):
        return self.helper.translate(self.web_post(), ((self.settings["mount_width"] / 2.0) + off_w, -(self.settings["mount_height"] / 2.0) - off_h, 0))

    def get_torow(self, column):
        return self.caps.bottom_key(column) + 1
        # torow = lastrow
        # if full_last_rows or (column == 4 and inner_column):
        #     torow = lastrow + 1
        #
        # if column in [0, 1]:
        #     torow = lastrow
        # return torow


    def connectors(self, ):
        logger.debug('connectors()')
        hulls = []
        for column in range(self.settings["ncols"] - 1):
            torow = self.get_torow( column)
            if not self.settings["full_last_rows"] and column == 3:
                torow -= 1

            for row in range(torow):  # need to consider last_row?
                # for row in range( nrows):  # need to consider last_row?
                places = []
                next_row = row if row <= self.caps.bottom_key(column + 1) else self.caps.bottom_key(column + 1)
                places.append(self.caps.key_place(self.web_post_tl(), column + 1, next_row))
                places.append(self.caps.key_place(self.web_post_tr(), column, row))
                places.append(self.caps.key_place(self.web_post_bl(), column + 1, next_row))
                places.append(self.caps.key_place(self.web_post_br(), column, row))
                hulls.append(self.helper.triangle_hulls(places))

        for column in range(self.settings["ncols"]):
            torow = self.get_torow( column)
            # for row in range( nrows-1):
            # next_row = row + 1 if row + 1 < bottom_key( column) else bottom_key( column)
            for row in range(torow - 1):
                places = []
                places.append(self.caps.key_place(self.web_post_bl(), column, row))
                places.append(self.caps.key_place(self.web_post_br(), column, row))
                places.append(self.caps.key_place(self.web_post_tl(), column, row + 1))
                places.append(self.caps.key_place(self.web_post_tr(), column, row + 1))
                hulls.append(self.helper.triangle_hulls(places))

        for column in range(self.settings["ncols"] - 1):
            torow = self.get_torow( column)
            # for row in range( nrows-1):  # need to consider last_row?
            for row in range(torow - 1):  # need to consider last_row?
                next_row = row if row < self.caps.bottom_key(column + 1) else self.caps.bottom_key(column + 1) - 1

                places = []
                places.append(self.caps.key_place(self.web_post_br(), column, row))
                places.append(self.caps.key_place(self.web_post_tr(), column, row + 1))
                places.append(self.caps.key_place(self.web_post_bl(), column + 1, next_row))
                places.append(self.caps.key_place(self.web_post_tl(), column + 1, next_row + 1))
                hulls.append(self.helper.triangle_hulls(places))

        return self.helper.union(hulls)

