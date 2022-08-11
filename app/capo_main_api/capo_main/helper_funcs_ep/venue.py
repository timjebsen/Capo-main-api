# Endpoint for adding an individual Gig to the db
# Duplicates/pre-exisitng data checks to be included...
import time
import sys
import traceback
import requests
import json
import re
from ..sql.sql_connector import connector_for_class_method
from ..helper_funcs import db_funcs as db_funcs
from ..helper_funcs import images as images
from ..helper_funcs import notices as n
from ..helper_funcs import global_vars as global_vars
from ..exceptions import *


class venue_helper:
    @connector_for_class_method
    def venue_exist(self, cursor, request):
        to_check_type = request.query['type']
        value_to_check = request.query['val']
        res = {}
        try:
            if db_funcs.check_exist(None, cursor, 'venues', to_check_type, value_to_check):
                if to_check_type == "google_place_id":
                    res['status'] = 'OK'
                    res['content'] = {
                        "exists": True,
                        "venue_id": db_funcs.get_uuid_from_id(None, cursor, db_funcs.get_id_using_triplej_or_gplacesid(None, cursor, "venues", value_to_check), "venue")
                    }
                # ! Only support for google place id currently
                # TODO implement support for name
            else:
                res['status'] = 'OK'
                res['content'] = {
                    "exists": False,
                }
            return res
        except Exception as e:
            print(e)
            res['status'] = 'FAIL'
            res['message'] = None
            return res

    @connector_for_class_method
    def add_venue_images(self, cursor):
        # Checks every venue if images exist
        # If not, then get images from google and upload to img server

        sql = "SELECT `uuid`, `has_img`, `google_place_id`  FROM `venues` WHERE `active` = True"
        cursor.execute(sql)
        venues = cursor.fetchall()
        num_of_no_images = 0
        num_of_updated = 0
        if len(venues) != 0:
            for each in venues:
                uuid = each[0]
                has_image = each[1]
                if not has_image:
                    # Venue does not have images
                    num_of_no_images += 1
                    places_id = each[2]
                    images_res = requests.get(global_vars.PLACES_DETAILS_BASE,
                                              params={
                                                  "place_id": places_id,
                                                  "fields": "photo",
                                                  "key": global_vars.PLACES_API_KEY
                                              })
                    images_res = images_res.json()
                    if images_res['status'] == 'OK':
                        try:
                            is_images_saved = images.save_places_venue_images(
                                None, images_res['result']['photos'], uuid)

                            if is_images_saved == 'success':
                                # Update row with has_img
                                sql = "UPDATE `venues` SET `has_img` = '1' WHERE `venues`.`uuid` = '{}'".format(
                                    uuid)
                                cursor.execute(sql)
                                print('Added new images')
                                num_of_updated += 1 
                            else:
                                raise SaveImageError(
                                    n.print_note(
                                        None, 1, "add_venue_images",
                                        "Error saving images. See log for details: {}"
                                        .format(is_images_saved)))
                        except DataError:
                            print('Error in saving images: Ignoring')
                            pass
                        except Exception as e:
                            print('Error in saving images: Ignoring')
                            print(e)

        res = {}
        res['status'] = 'OK'
        res['message'] = '{} venues had no images. Updated {} venues'.format(num_of_no_images, num_of_updated)
        return res

    @connector_for_class_method
    def deactivate_closed_venues(self, cursor):
        sql = "SELECT `uuid`, `google_place_id`, `name`  FROM `venues` WHERE `active` = True"
        cursor.execute(sql)
        venues = cursor.fetchall()
        venues_deactivated = 0
        if len(venues) != 0: 
            for each in venues:
                venue_id = each[0]
                places_id = each[1]
                venue_name = each[2]
                venue_det_res = requests.get(global_vars.PLACES_DETAILS_BASE,
                                                params={
                                                    "place_id": places_id,
                                                    "fields": "business_status",
                                                    "key": global_vars.PLACES_API_KEY
                                                })

                venue_det_res = venue_det_res.json()
                if venue_det_res['status'] == 'OK':
                    print(venue_det_res)
                    try:
                        if venue_det_res['result']['business_status'] == 'CLOSED_PERMANENTLY':
                            # Change venue active to false
                            sql = "UPDATE `venues` SET `active`= False WHERE `uuid` = '{}'".format(venue_id)
                            cursor.execute(sql)
                            print('Venue: {} is closed. Changing active status'.format(venue_name))
                            venues_deactivated += 1
                    except KeyError:
                        print('No business_status found for:')
                        print(venue_det_res)
        res = {}
        res['status'] = 'OK'
        res['message'] = '{} - venues deactivated'.format(venues_deactivated)
        return res