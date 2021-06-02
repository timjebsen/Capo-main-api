# Endpoint for adding an individual Gig to the db
# Duplicates/pre-exisitng data checks to be included...
import time
import sys
import traceback
import requests
import json
import re
from ..sql.sql_connector import connector_for_class_post_method
from ..helper_funcs import db_funcs as db_funcs
from ..helper_funcs import images as images
from ..helper_funcs import notices as n
from ..helper_funcs import global_vars as global_vars
from ..exceptions import *
from ..sql.config import config as config

# Expected data model
# venue_info_model = {
#         "address": str(null),
#         "description": str(null),
#         "google_place_id": str(not null),
#         # "has_img": bool(not null), add images function will update this value
#         "hours_formatted": list(not null),
#         "hours_raw": list(not null),
#         "price_rating": int(null),
#         "rating": str(null),
#         "socials": {
#             "fb_link": str(null),
#             "website": str(null)
#         },
#         "suburb": str(null),
#         "venue_name": str(not null),
#         "venue_type": list(null),
#         "coords": dict(str(), float(), not null),
#         "source_name":
# }

# Create a new venue record.
# * All venue information must be sourced from places API.
# * This function must only be run after the venue
# * has been matched with a place from Places API

# * Images - If venue_info has images. Get images from google, and save to images api. And update has_img field


class post_venue:
    # Check if a liat or singular venue obj
    @connector_for_class_post_method
    def post_venue(self, cursor, data):
        try:
            res = "Begin post_venue"
            venue_data = data
            # print(json.dumps(venue_data))
            if type(venue_data) != dict:
                raise DataType(
                    n.print_note(None, 2, "post_venue",
                                 "Data not a dict. See logs for details"))

            # Check if venue obj is a list of venues
            if "venues" in venue_data:
                venue_list = venue_data["venues"]
                res = post_venue_list(cursor, venue_list)

            # basic check for field existence
            # elif len(venue_data) == 12:
            else:
                res = post_venue_ind(cursor, venue_data)

            # else:
            #     raise DataFormat(n.print_note(None, 2, "post_venue", "Unknown dict format or objects. See logs for details"))

        except (DataFormat, DataType) as e:
            print(str(e))
            res = {
                "status": "fail",
                "message": "Failed to creat new venue",
                "detailed": str(e),
                "data_recieved": venue_data
            }

        except Exception as e:
            n.print_note(
                None, 2, "post_venue",
                "Unexpected error in post_venue. See logs for details")
            traceback.print_exc()
            res = {
                "status": "fail",
                "message": "Failed to creat new venue",
                "detailed": str(e),
                "data_recieved": venue_data
            }

        return res

    @connector_for_class_post_method
    def update(self, cursor, data):
        try:
            new_venue_info = data['venue_info']
            new_fb_link = new_venue_info['facebook_link']
            new_desc = new_venue_info['description']
            new_web = new_venue_info['website']
            _id = new_venue_info['id']

            # Nullify empty-ish strings
            # TODO move to helper func
            for key in new_venue_info:
                if new_venue_info[key] == "" or new_venue_info[
                        key] == "None" or new_venue_info[
                            key] == " " or str.isspace(new_venue_info[key]):
                    new_venue_info[key] = None

            sql = "UPDATE `venues` SET `facebook_link` = %s, `description` = %s, `website` = %s WHERE venues.uuid = %s;"
            val = (new_fb_link, new_desc, new_web, _id)

            try:
                cursor.execute(sql, val)
                res = {
                    "status": "OK",
                    "message": "Updated venue",
                    "detailed": _id,
                    "data_recieved": data
                }

            except Exception as e:
                n.print_note(
                    None, 2, "update venue",
                    "Unexpected error when UPDATE value. Data recived")
                print(e)
                raise Exception(e)

        except Exception as e:
            traceback.print_exc()
            res = {
                "status": "FAIL",
                "message": "Failed to update venue",
                "detailed": str(e),
                "data_recieved": data
            }
            n.print_note(
                None, 2, "update venue",
                "Unexpected error. See logs for details. Data recived:\n" +
                str(res))

        return res

    @connector_for_class_post_method
    def deactivate(self, cursor, data):
        try:
            venue_info = data['venue_info']
            _id = venue_info['id']

            sql = "UPDATE `venues` SET `active` = 0 WHERE venues.uuid = %s;"
            val = (_id)

            try:
                cursor.execute(sql, val)
                res = {
                    "status": "OK",
                    "message": "Deactivated venue",
                    "detailed": _id,
                    "data_recieved": data
                }

            except Exception as e:
                n.print_note(
                    None, 2, "deactivate venue",
                    "Unexpected error when UPDATE value. Data recived")
                print(e)
                raise Exception(e)

        except Exception as e:
            traceback.print_exc()
            res = {
                "status": "FAIL",
                "message": "Failed to deactivate venue",
                "detailed": str(e),
                "data_recieved": data
            }
            n.print_note(
                None, 2, "deactivate venue",
                "Unexpected error. See logs for details. Data recived:\n" +
                str(res))

        return res


# Takes a venue venue obj.
# Checks for duplicate, and creates a new venue
def post_venue_ind(cursor, venue_info):
    res = "Attempting to post_venue_ind"
    try:
        # ! These are hardcoded for time being.
        # ! It is assumed that all sources
        # ! are from places API
        source_name = "Google Places API"
        source_link = "https://maps.googleapis.com/maps/api/place"

        # Check source exists and get source ID
        source_id = db_funcs.get_source_id(None, cursor, source_name)

        places_id = venue_info["place_id"]

        if (places_id == ''):
            res = n.print_note(None, 2, "post_venue",
                               "places_id cannont be empty")
            raise DataError()

        # Build the coordinate
        coordinate = "PointFromText('POINT({} {})')".format(
            venue_info['coordinate']['lng'], venue_info['coordinate']['lat'])

        try:
            website = venue_info['socials']['website'],
            fb_link = venue_info['socials']['facebook_link']
        except KeyError:
            website = None
            fb_link = None

        venue_model = {
            "name": venue_info['name'],
            "address": venue_info['address'],
            "suburb": venue_info['suburb'],
            "hours_weekday": venue_info['hours_weekday'],
            "hours_raw": venue_info['hours_raw'],
            "rating": venue_info['rating'],
            "socials": {
                "website": website,
                "facebook_link": fb_link
            },
            "google_place_id": venue_info['place_id'],
            "description": venue_info['description'],
            "coordinate": coordinate,
            "has_img": 0,
            "types": venue_info['types']
        }

        # Values to check for existence
        # * Uses place_id as a unique identifier to match against.
        table = "venues"
        column = "google_place_id"

        if not db_funcs.check_exist(None, cursor, table, column, places_id):
            # TODO find simpler alternative to SQL var parameters
            sql = "INSERT INTO `venues` (source_id, name, address, suburb, hours_weekday, hours_raw, rating, google_place_id, uuid, has_img, description, website, facebook_link) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, UUID(), %s, %s, %s, %s)"
            val = (source_id, venue_model["name"], venue_model["address"],
                   venue_model["suburb"], str(venue_model["hours_weekday"]),
                   str(venue_model["hours_raw"]), venue_model["rating"],
                   places_id, venue_model['has_img'],
                   venue_model['description'],
                   venue_model['socials']['website'],
                   venue_model['socials']['facebook_link'])
            try:
                cursor.execute(sql, val)
            except Exception as e:
                print('FAILED TO ADD VENUE')
                print(e)
                raise Exception

            # Get the id from the response and update the venue_types
            last_id = cursor.lastrowid

            # Get uuid using id
            last_uuid = db_funcs.get_uuid_from_id(None, cursor, last_id,
                                                  'venue')
            # Add last uuid to venue_model for response message
            venue_model['venue_id'] = last_uuid

            # Update the coordinates. This has to be done as a seperate command
            # because parameter binding returns the command as a literal string
            sql = "UPDATE `venues` SET `coordinate`= PointFromText('POINT({} {})') WHERE `venue_id` = {}".format(
                venue_info['coordinate']['lng'],
                venue_info['coordinate']['lat'], last_id)
            cursor.execute(sql)

            # Update types
            # For time being. The venue_types is complete
            # in that no new types should be created.
            # Any types that are not in the table, are ignored
            # TODO Create a 'tags' table to define more types i.e. vibe, atmosphere etc...
            if (venue_model['types'] != None and venue_model['types'] != []):
                for a_type in venue_model['types']:
                    sql = "SELECT `id` FROM `venue_types` WHERE `type` = %s"
                    val = (a_type, )
                    cursor.execute(sql, val)
                    resp = cursor.fetchone()

                    # Match with type
                    # get type id, and update venue_type
                    if (resp != None):
                        type_id = resp[0]
                        sql = "INSERT INTO `venue_type`(`venue_id`, `type_id`) VALUES (%s, %s)"
                        vals = (
                            last_id,
                            type_id,
                        )
                        cursor.execute(sql, vals)

            # Get and upload images to images server image_server to download images
            # TODO Refactor to helper func
            if (venue_info['images'] != None and venue_info['images'] != []):
                try:
                    is_images_saved = images.save_places_venue_images(
                        None, venue_info['images'], last_uuid)
                    if is_images_saved == 'success':
                        # Update row with has_img
                        sql = "UPDATE `venues` SET `has_img` = '1' WHERE `venues`.`uuid` = '{}'".format(
                            last_uuid)
                        cursor.execute(sql)
                    else:
                        raise SaveImageError(
                            n.print_note(
                                None, 1, "post_venue_ind",
                                "Error saving images. See log for details: {}".
                                format(is_images_saved)))
                except DataError:
                    print('Error in saving images: Ignoring')
                    pass
                except Exception as e:
                    print(e)

            res = {}
            res['status'] = 'OK'
            res['note'] = n.print_note(
                None, 0, "post_venue_ind",
                "Successfully Added: {}".format(venue_info["name"]))
            res['details'] = venue_model

        else:
            # TODO If already exists, check for differences and update accordingly... i.e. description/hours have changed/has images

            res = {}
            res['status'] = 'OK'
            res['note'] = n.print_note(
                None, 0, "post_venue_ind",
                "Already Exists: {}".format(venue_info["name"]))
            # venue_model['venue_id'] = db_funcs.ge
            res['details'] = venue_model

    except KeyError:
        traceback.print_exc()
        res = n.print_note(
            None, 2, "post_venue_ind", "Incomplete data for venue: " +
            venue_info["name"] + "\nSkipping...")

    except:
        res = n.print_note(
            None, 2, "post_venue_ind",
            "Unexpected error in post_venue_ind:" + str(sys.exc_info()[0]))
        traceback.print_exc()

    return res


def post_venue_list(cursor, venue_list):
    try:
        for i in range(len(venue_list)):
            venue_info = venue_list[str(i)]
            post_venue_ind(cursor, venue_info)
    except:
        res = n.print_note(
            None, 2, "post_venue_list",
            "Unexpected error iterating through post_venue_list data:" +
            str(sys.exc_info()[0]))
        traceback.print_exc()
    return res


# When creating a new venue, it must first be matched with a google places ID
# Takes a string to search for a venue with a mathcing name. Returns a slim venue obj
# The venue must then be confirmed by a user. Once verified, get_place_details is used to
# to get full venue obj
def get_places_id(request):
    try:
        s_venue_name = request.query['venue_name']

        if '&' in s_venue_name:
            s_venue_name = s_venue_name.replace('&', 'and')
        elif '%26' in s_venue_name:
            s_venue_name = s_venue_name.replace('%26', 'and')

        base = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input="
        params = "&inputtype=textquery&fields=formatted_address,name,types,place_id&locationbias=circle:2000000@-27.469911,153.026742"
        API_KEY = "&key=" + global_vars.PLACES_API_KEY
        build_url = base + s_venue_name + params + API_KEY
        place_res = requests.get(build_url)
        place_res = json.loads(place_res.content)

        res = {}

        if (place_res == None or place_res == {}):
            res['status'] = 'Empty response from request. See log for details'
            raise DataError(
                n.print_note(
                    None, 2, "get_places_id",
                    "Unexpected error. No data returned:" + sys.exc_info()[0]))

        elif (place_res['status'] == 'ZERO_RESULTS'):
            res['status'] = 'No place found with name as: {}'.format(
                s_venue_name)
            raise DataError(
                n.print_note(
                    None, 2, "get_places_id",
                    "No place found with name as: {}".format(s_venue_name)))

        elif (place_res['status'] == 'OK'):
            res['status'] = place_res['status']
            res['content'] = place_res['candidates']
            return res

    except DataError:
        return res

    except KeyError as e:
        n.print_note(None, 2, "get_places_id",
                     "Unknown error ocurred: {}".format(str(e)))
        res['status'] = 'Key error: ' + str(e)
        return res

    except Exception as e:
        n.print_note(None, 2, "get_places_id",
                     "Unknown error ocurred: {}".format(str(e)))
        res['status'] = 'Unknown error ocurred. See log for details'
        return res


# Takes a place_id and returns a venue obj
def get_place_details(request):
    try:
        place_id = request.query['place_id']
        base = "https://maps.googleapis.com/maps/api/place/details/json?place_id="
        params = "&fields=formatted_address,geometry,name,opening_hours,photos,rating,price_level,types,website,address_components"
        API_KEY = "&key=" + global_vars.PLACES_API_KEY
        build_url = base + place_id + params + API_KEY
        place_res = requests.get(build_url)
        place_res = json.loads(place_res.content)

        res = {}

        if (place_res == None or place_res == {}):
            res['status'] = 'Could not reach maps.googleapis.com. Check internet connection. Please notify admin'
            raise DataError(
                n.print_note(
                    None, 2, "get_place_details",
                    "Could not reach maps.googleapis.com. Check internet connection:"
                    + sys.exc_info()[0]))

        elif (place_res['status'] == 'ZERO_RESULTS'):
            res['status'] = 'No place found with place_id: {}'.format(place_id)
            raise DataError(
                n.print_note(
                    None, 2, "get_place_details",
                    "No place found with place_id: {}".format(place_id)))

        elif (place_res['status'] == 'OK'):
            res['status'] = place_res['status']
            venue_info = place_res['result']

            # Theres probably a better way of doing this
            try:
                hours_weekday = venue_info['opening_hours']['weekday_text']
                hours_raw = venue_info['opening_hours']['periods']
            except:
                hours_weekday = None
                hours_raw = None

            try:
                rating = venue_info['rating']
            except:
                rating = None

            try:
                website = venue_info['website']
            except:
                website = None

            try:
                images = venue_info['photos']
            except:
                images = None

            try:
                types = venue_info['types']
            except:
                types = None

            try:
                address_components = venue_info['address_components']
            except:
                address_components = None

            try:
                rebuilt_venue_model = {
                    "name": venue_info['name'],
                    "address": venue_info['formatted_address'],
                    "suburb": get_suburb(venue_info),
                    "hours_weekday": hours_weekday,
                    "rating": rating,
                    "socials": {
                        "website": website,
                        "facebook_link": None
                    },
                    "place_id": place_id,
                    "description": None,
                    "coordinate": venue_info['geometry']['location'],
                    "hours_raw": hours_raw,
                    "images": images,
                    "types": types
                }

                res['content'] = rebuilt_venue_model
            except:
                res['status'] = "Error building venue info"
                print(
                    n.print_note(
                        None, 2, "get_places_id",
                        "Unexpected error. No data returned:" +
                        sys.exc_info()[0]))

            return res

    except DataError:
        return res

    except KeyError as e:
        n.print_note(None, 2, "get_places_id",
                     "Unknown error ocurred: {}".format(str(e)))
        res['status'] = 'Key error: ' + str(e)
        return res

    except Exception as e:
        n.print_note(None, 2, "get_places_id",
                     "Unknown error ocurred: {}".format(str(e)))
        res['status'] = 'Unknown error ocurred. See log for details'
        return res


def get_suburb(new_venue_info):
    try:
        if (new_venue_info['address_components'] != None
                and new_venue_info['address_components'] != []
                and type(new_venue_info['address_components']) is list):
            # Iterate over address components, and check the 'types' contains 'locality'
            # Components = [{
            #     "long_name" : "Southport",
            #     "short_name" : "Southport",
            #     "types" : [ "locality", "political" ]
            #  }]

            for each_comp in new_venue_info['address_components']:
                if ('locality' in each_comp['types']):
                    # Return the short_name
                    return each_comp['short_name']
    except Exception as e:
        print(
            n.print_note(None, 2, "get_suburb",
                         "Unknown error ocurred: {}".format(str(e))))

    # If first method fails, try second method
    try:
        # * This is an old method of extracting suburb for a venue and might not be as reliable
        # ! Uses 'QLD' as identifier. Will need to be changed when going national
        print('Trying alternative get_suburb method')
        extr_sub = re.findall(r"(.*) QLD [0-9]*, Australia$",
                              new_venue_info['formatted_address'])
        if extr_sub:
            if ("," in extr_sub[0]):
                extr_sub2 = re.findall(r", (.*)", extr_sub[0])
                if extr_sub2:
                    suburb = extr_sub2[0]
            else:
                suburb = extr_sub[0]
        elif new_venue_info['formatted_address']:
            if ("," in new_venue_info['formatted_address']):
                extr_sub = re.findall(r", (.*)",
                                      new_venue_info['formatted_address'])
                if extr_sub:
                    suburb = extr_sub2[0]
            else:
                suburb = None
        else:
            # Suburb Extract failed
            suburb = None

        return suburb

    except:
        suburb = None
        return suburb
