import re
import time
import traceback
import json
from datetime import datetime
from datetime import date as dtdate
from datetime import timedelta
from datetime import time as dttime
import requests
from .exceptions import *
from uuid import UUID
import inspect
import ast
from .sql.config import Config


# Helper functions
# TODO Refactor... this...
class h_funcs:
    # Print information about each request in terminal
    def print_req_info(self, request):
        # Add time delay
        # time.sleep(2)
        global changed
        global_vars.REQUEST_NUM += 1
        print("======== Begin Request ========")
        print("Server time: {}".format(datetime.now().strftime("%H:%M:%S.%f")))
        print("Request: {}".format(request.path))
        print("Global Req. number: ", global_vars.REQUEST_NUM)
        print("Client: " + request.host)
        print("Origin IP: " + request.remote)
        # print("========= End Request =========")

    # Next weekday. Used in "get rest of week" function
    def next_weekday(self, d, weekday):
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return d + timedelta(days_ahead)

    def is_valid_uuid(self, uuid_to_test, version=1):
        """
        Check if uuid_to_test is a valid UUID.
        
        Parameters
        ----------
        uuid_to_test : str
        version : {1, 2, 3, 4}
        
        Returns
        -------
        `True` if uuid_to_test is a valid UUID, otherwise `False`.
        
        Examples
        --------
        >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
        True
        >>> is_valid_uuid('c9bf9e58')
        False
        """

        try:
            uuid_obj = UUID(uuid_to_test, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == uuid_to_test

# Database helper functions
# TODO Refactor... this...
class db_funcs():

    def add_to_artist_genres(self, cursor, artist_id, genre_id):
        sql = "INSERT INTO `artist_genres` (artist_id, genre_id) VALUES (%s, %s)"
        val = (
            artist_id,
            genre_id,
        )
        cursor.execute(sql, val)

    def check_exist(self, cursor, tbl, col, value_to_check):
        sql = "SELECT 1 FROM `{}` WHERE `{}` = %s".format(tbl, col)
        val = (value_to_check, )
        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        exists = False
        if myresult:
            exists = True
        return exists

    def get_source_id(self, cursor, src_name, src_link=None):
        table = "sources"
        column = "name"

        if not db_funcs.check_exist(None, cursor, table, column, src_name):
            try:
                sql = "INSERT INTO `sources` (name, link) VALUES (%s, %s);"
                val = (src_name, src_link)
                cursor.execute(sql, val)
                source_id = cursor.lastrowid
                return source_id
            except Exception:
                traceback.print_exc()
                notices.print_note(None, 2, "get_source_id", "Error tryng to create a new source")      
        else:
            try:
                sql = "SELECT * FROM `sources` WHERE `name` = %s"
                val = (src_name, )
                cursor.execute(sql, val)
                myresult = cursor.fetchall()
                source_id = myresult[0][0]
                return source_id
            except Exception:
                traceback.print_exc()
                notices.print_note(None, 2, "get_source_id", "Error trying to retrieve source record")
        return 15 # use 'unknown' 
        # TODO handle get source id errors
    
    def get_user_id(self, cursor, user_name):
        try:
            sql = "SELECT * FROM `users` WHERE `name` = %s"
            val = (user_name, )
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            source_id = myresult[0][0]
            return source_id
        except Exception:
            traceback.print_exc()
            notices.print_note(None, 2, "get_user_id", "Error trying to retrieve source record")
        return 5 # use 'unknown' 
        # TODO handle get user id errors

    def get_id_using_triplej_or_gplacesid(self, cursor, tbl, val):
        if tbl == "venues":
            id_col = "venue_id"
            col = "google_place_id"
        elif tbl == "artists":
            id_col = "artist_id"
            col = "unearthed_href"
        elif tbl == "users":
            id_col = "user_id"
            col = "name"
        elif tbl == "sources":
            id_col = "source_id"
            col = "link"
        else:
            print("Error: no tables named: {}".format(tbl))

        sql = "SELECT `{}` FROM `{}` WHERE `{}` = %s".format(id_col, tbl, col)
        val = (val, )
        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        try:
            row_id = myresult[0][0]
        except IndexError:
            print(
                "Get_id: Error: No content in response. Val: {}, Tbl: {}, Col: {}"
                .format(val, tbl, col))

        return row_id

    # Returns a bool for a given uuid if exists in artists table
    # Used to identify what table the uuid belongs to
    def is_artist_from_uuid(self, cursor, uuid):
        sql = "SELECT 1 FROM `artists` WHERE `uuid` = '{}'".format(uuid)
        cursor.execute(sql)
        myresult = cursor.fetchall()
        if (len(myresult) > 1):
            notices.print_note(None, 2, "is_artist_from_uuid",
                               "More than 1 record with uuid: {}".format(uuid))
            raise Exception
        elif (len(myresult) == 1):
            return True
        else:
            return False

    # Returns a bool for a given uuid if exists in venues table
    # Used to identify what table the uuid belongs to
    def is_venue_from_uuid(self, cursor, uuid):
        sql = "SELECT 1 FROM `venues` WHERE `uuid` = '{}'".format(uuid)
        cursor.execute(sql)
        myresult = cursor.fetchall()
        if (len(myresult) > 1):
            notices.print_note(None, 2, "is_venue_from_uuid",
                               "More than 1 record with uuid: {}".format(uuid))
            raise Exception
        elif (len(myresult) == 1):
            return True
        else:
            return False

    # Returns internal id of either artist or venue from a uuid
    # Throws error if more than one uuid is matched (very rare, but possible)
    def get_id_from_uuid(self, cursor, uuid):
        is_artist = db_funcs.is_artist_from_uuid(None, cursor, uuid)
        is_venue = db_funcs.is_venue_from_uuid(None, cursor, uuid)

        # Make sure the given uuid doesnt exist in both tables
        if (is_artist and is_venue):
            raise Exception

        elif (is_artist == True):
            sql = "SELECT `artist_id` FROM `artists` WHERE `uuid` = '{}'".format(
                uuid)
            cursor.execute(sql)
            myresult = cursor.fetchall()
            return myresult[0][0]

        elif (is_venue == True):
            sql = "SELECT `venue_id` FROM `venues` WHERE `uuid` = '{}'".format(
                uuid)
            cursor.execute(sql)
            myresult = cursor.fetchall()
            return myresult[0][0]
        else:
            raise UUIDNotFound(
                notices.print_note(
                    None, 2, "get_id_from_uuid",
                    "No artist or venue with uuid: {}".format(uuid)))

    # Get a uuid from an id. Only for venues and artists
    def get_uuid_from_id(self, cursor, _id, artist_or_venue):
        if _id:
            if (artist_or_venue == 'artist'):
                sql = "SELECT `uuid` FROM `artists` WHERE `artist_id` = '{}'".format(
                    _id)
                cursor.execute(sql)
                myresult = cursor.fetchall()
                return myresult[0][0]

            elif (artist_or_venue == 'venue'):
                sql = "SELECT `uuid` FROM `venues` WHERE `venue_id` = '{}'".format(
                    _id)
                cursor.execute(sql)
                myresult = cursor.fetchall()
                return myresult[0][0]
            else:
                raise IDNotFound(
                    notices.print_note(
                        None, 2, "get_uuid_from_id",
                        "No artist or venue with id: {}".format(_id)))
        return notices.print_note(None, 2, "get_uuid_from_id", "Id is None")

    # Returns an internal id based off a name only match
    # Used in the post_event handler func. This must be deprecated in near future
    # because of high chances of name duplicates with a larger dataset.
    # Only used for MVP development.
    def get_id_from_name(self, cursor, _type, name):
        if (_type == 'venue'):
            sql = "SELECT `venue_id` FROM `venues` WHERE `name` = %s"
            val = (name, )
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            if (len(myresult) > 1):
                notices.print_note(
                    None, 2, "get_id_from_name",
                    "More than 1 record with name: {}".format(name))
                raise MoreThanOneRecordReturned(
                    notices.print_note(
                        None, 2, "get_id_from_name",
                        "More than 1 record with name: {}".format(name)))
            elif (len(myresult) == 1):
                return myresult[0][0]
            else:
                raise IDNotFound(
                    notices.print_note(None, 2, "get_id_from_name",
                                       "No venue with name: {}".format(name)))

        elif (_type == 'artist'):
            sql = "SELECT `artist_id` FROM `artists` WHERE `name` = %s"
            val = (name, )
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            if (len(myresult) > 1):
                raise MoreThanOneRecordReturned(
                    notices.print_note(
                        None, 2, "get_id_from_name",
                        "More than 1 record with name: {}".format(name)))
            elif (len(myresult) == 1):
                return myresult[0][0]
            else:

                raise RecordNotFound(
                    notices.print_note(None, 2, "get_id_from_name",
                                       "No artist with name: {}".format(name)))
        else:
            raise CategoryError(
                notices.print_note(
                    None, 2, "get_id_from_name",
                    "Type must be 'artist' or 'venue', given: {}".format(
                        _type)))

    def get_region(self, cursor, id):
        region = {}

        sql = "SELECT * FROM `regions` WHERE `reg_id` = '{}'".format(id)
        cursor.execute(sql)
        myresult = cursor.fetchall()
        try:
            res = myresult[0]
            region = {"region": res[1], "state_abr": res[3]}

        except IndexError:
            notices.print_note(None, 2, "get_region",
                               "No region with id of: {}".format(id))

        return region

    def get_genre(self, cursor, _id):
        genre = []
        if (not isinstance(_id, int) and h_funcs.is_valid_uuid(None, _id)):
            _id = db_funcs.get_id_from_uuid(None, cursor, _id)

        if (isinstance(_id, int)):
            sql = "SELECT * FROM `artist_genres` WHERE `artist_id` = '{}' ORDER BY `artist_genres`.`genre_id` ASC ".format(
                _id)
            genre_id_list = []
            cursor.execute(sql)
            result = cursor.fetchall()
            try:
                # res = myresult[0]
                g_id_old = None
                for each in result:
                    # * Check for difference only done due to double ups in dev database.
                    g_id_new = each[1]
                    if (g_id_old == None):
                        genre_id_list.append(g_id_new)
                        g_id_old = g_id_new
                    elif (g_id_new != g_id_old):
                        genre_id_list.append(g_id_new)
                        g_id_old = g_id_new
            except IndexError:
                notices.print_note(
                    None, 2, "get_genre",
                    "Artist id not found in artist genre tbl. ID of: {}".
                    format(_id))

            for each in genre_id_list:
                sql = "SELECT * FROM `genres` WHERE `genre_id` = {}".format(
                    each)
                cursor.execute(sql)
                result = cursor.fetchall()
                res = result[0]
                genre.append(res[1])
        else:
            notices.print_note(None, 2, "get_genre",
                               "ID is wrong format: {}".format(id))
        return genre

    def get_venue_types(self, cursor, id):
        type_string = []
        if (isinstance(id, int)):
            sql = "SELECT * FROM `venue_type` WHERE `venue_id` = {} ORDER BY venue_type.type_id ASC ".format(
                id)
            type_id_list = []
            cursor.execute(sql)
            myresult = cursor.fetchall()
            try:
                # res = myresult[0]
                t_id_old = None
                for each in myresult:
                    # * Check for difference only done due to double ups in dev database.
                    t_id_new = each[1]
                    if (t_id_old == None):
                        type_id_list.append(t_id_new)
                        t_id_old = t_id_new
                    elif (t_id_new != t_id_old):
                        type_id_list.append(t_id_new)
                        t_id_old = t_id_new
            except IndexError:
                notices.print_note(
                    None, 2, "get_venue)type",
                    "Venue id not found in venue type tbl. ID of: {}".format(
                        id))

            for each in type_id_list:
                sql = "SELECT * FROM `venue_types` WHERE `id` = {}".format(
                    each)
                cursor.execute(sql)
                myresult = cursor.fetchall()
                res = myresult[0]
                type_string.append(res[1])
        else:
            notices.print_note(None, 2, "get_venue",
                               "ID must be uuid: given {}".format(id))
        return type_string

    # TODO move to event_h_funcs class and refactor dupliacate and confilct checks
    def insert_event(self, cursor, event_info):
        try:
            if (type(event_info) != dict):
                notices.print_note(
                    None, 2,
                    "insert_event", "event_info must be dict: given {}".format(
                        type(event_info)))
                raise Exception

            # Check for a duplicate - same artist, venue, time, date
            elif (event_h_funcs.check_event_duplicate(None, cursor,
                                                      event_info['artist_id'],
                                                      event_info['venue_id'],
                                                      event_info['time'],
                                                      event_info['date'])):
                # TODO check for new info
                raise Duplicate(
                    notices.print_note(
                        None, 0, "insert_event",
                        "Event already exists: {}".format(str(event_info))))


            # TODO below
            # Otherwise if the event is actually the same, we check to see
            # if new information is present (description, real artist, etc...).
            # Then update the event with the new information.

            # Data points to consider:
            # - Title/Artist. If the new artist is a real artist (not a temp), update accordingly.
            # - If no description is present in the current event, but the new event has one, update acordingly.

            elif (event_h_funcs.check_event_conflict(None, cursor,
                                                event_info['time'],
                                                event_info['venue_id'],
                                                event_info['date'])):
                
                # event_h_funcs.compare_event_fields(None, cursor, event_info)
     
                # Add event with pending = true and active = false
                try:
                    sql = "INSERT INTO `gigs`(`artist_id`, `venue_id`, `user_id`, `source_id`, `ticket`, `date`, `time`, `price`, `facebook_event_link`, `uuid`, `duration`, `description`, `event_link`, `pending`, `active`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, UUID(), %s, %s, %s, 1, 0)"
                    vals = (event_info['artist_id'], event_info['venue_id'],
                            event_info['user_id'], event_info['source_id'],
                            event_info['ticket'], event_info['date'],
                            event_info['time'], event_info['price'],
                            event_info['facebook_event_link'],
                            event_info['duration'], event_info['description'],
                            event_info['event_link'])
                    cursor.execute(sql, vals)

                except Exception as e:
                    traceback.print_exc()
                    print(e)
                    
                raise EventConflict(
                    notices.print_note(
                        None, 0, "insert_event",
                        "Conflicting event: {}\nVenue already has an event during this time with different title".format(str(event_info))))
                

            else:
                try:
                    sql = "INSERT INTO `gigs`(`artist_id`, `venue_id`, `user_id`, `source_id`, `ticket`, `date`, `time`, `price`, `facebook_event_link`, `uuid`, `duration`, `description`, `event_link`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, UUID(), %s, %s, %s)"
                    vals = (event_info['artist_id'], event_info['venue_id'],
                            event_info['user_id'], event_info['source_id'],
                            event_info['ticket'], event_info['date'],
                            event_info['time'], event_info['price'],
                            event_info['facebook_event_link'],
                            event_info['duration'], event_info['description'],
                            event_info['event_link'])
                    cursor.execute(sql, vals)
                    res = {
                        "status": "OK",
                        "message": "Succesfully created new event"
                    }
                    return res

                except Exception as e:
                    traceback.print_exc()
                    print(e)

        except Duplicate:
            # Events are sometimes posted across multiple locations
            # that are scraped, and sometimes those events contain
            # data we dont already have. We check to see if the new
            # event holds any new information and update the old event.
            #
            # Pseudocode:
            # iterate through each data point
            # compare with old data
            # if old data is empty, insert new data
            # If the new event data is not a stub (not matched with an artist) and if the old data is a stub.
            # Replace the old data 'artist_id' with the new 'artist_id'
            # Remove old stub?
            # TODO implement above

            res = {
                "status": "OK",
                "message": "Event Already Exists",
            }
            return res
        
        except EventConflict:
            res = {
                "status": "OK",
                "message": "Conflicting event. Venue already has an event at this time. Please review in admin tool.",
            }
            return res
    
    def get_source_name(self, cursor, source_id):
        try:
            sql = "SELECT `name` FROM `sources` WHERE `source_id` = %s"
            val = (source_id, )
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            source_name = myresult[0][0]
            return source_name
        except:
            notices.print_note(None, 1, "get_source_name",
                                   "Error retriving source name for id: {}".format(source_id))

            return None
        
    def get_name_of_user(self, cursor, user_id):
        try:
            sql = "SELECT `name` FROM `users` WHERE `user_id` = %s"
            val = (user_id, )
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            user_name = myresult[0][0]
            return user_name
        except:
            notices.print_note(None, 1, "get_name_of_user",
                                   "Error retriving user name for id: {}".format(user_id))

            return None

class notices:
    def print_note(self, type, func, details):
        # * 0 == Notice
        # * 1 == Warning
        # * 2 == Error

        # for each in inspect.stack():
        #     if each[0].f_globals['__name__'] == '__main__':
        #         break
        #     print(each[0].f_globals['__name__'])
        #     # print(inspect.getmembers(each[0].f_globals))

        notice_type = ""
        if (type == 0):
            notice_type = "[NOTICE]"
        elif (type == 1):
            notice_type = "[WARNING]"
        elif (type == 2):
            notice_type = "[ERROR]"

        notice = notice_type + " " + func + ": " + details
        print(notice)
        return notice


# Build response: Append meta data, custom and default
class response_builder:
    def build_res(self, list_obj, type_of, request, stime, custom=None):
        res = {}
        num = 0
        if type(list_obj) is dict:
            for each in list_obj:
                num += len(list_obj[each])
        elif type(list_obj) is list:
            num += len(list_obj)

        meta_data = {
            "rqst": request.path,
            "time_rcvd": stime,
            "time_sent": time.time(),
            "time_total": str((time.time() - stime) * 1000) + ' ms',
            "num_of_obj": num,
        }

        # Update metadata with custom fields
        if custom:
            for key, val in custom.items():
                meta_data[key] = val

        res = {type_of: list_obj, "meta": meta_data}
        return res

    def build_meta(self, gig_list, group_mode):
        num = 0
        for each in gig_list:
            num += len(gig_list[each])
        meta_data = {"num_of_obj": num, "group_mode": group_mode}
        return meta_data


# TODO move to config file
class global_vars:
    img_api_host = Config.get('images')['api_host']
    img_handler = '/handler'
    add_image_ep = img_handler + '/image'

    img_server = Config.get('images')['server_host']
    img_dir = '/assets/img'
    venue_img_dir = img_dir + '/venues/'
    artist_img_dir = img_dir + '/artists/'

    PLACES_API_KEY = ""
    PLACES_PHOTOS_URL = "https://maps.googleapis.com/maps/api/place/photo"
    PLACES_DETAILS_BASE = "https://maps.googleapis.com/maps/api/place/details/json"

    REQUEST_NUM = 0


class images:
    # If it takes more than 2 seconds to connect to the image server
    # there is probably an issue. Because this will run for every venue in the list,
    # it will take a very long a time to finish.
    # Therefore skip the get_image_links for the remaining venues.
    # When a new request is received check again for image server connection.
    # * If it can reconnect to the image server, it will miss the first venue on the first re-try.
    ignore_images = False

    def get_image_links(self, artist_or_ven, uuid):
        image_links = {}
        if not images.ignore_images:
            if (artist_or_ven == 'venue'):
                url = Config.get('images')['server_host']+global_vars.venue_img_dir + uuid
                
            elif (artist_or_ven == 'artist'):
                url = Config.get('images')['server_host']+global_vars.artist_img_dir + uuid
            try:
                
                req = requests.get(url, timeout=2)
                if (req.status_code == 200):
                    ex = r"href=\"("
                    ex1 = r"\d*\..*)\""
                    reg_patt = ex + ex1
                    matches = re.findall(reg_patt, req.text)
                    for each_match in matches:
                        if (each_match[2] == 0):
                            image_links[0] = url + '/' + each_match
                        else:
                            image_links[len(
                                image_links)] = url + '/' + each_match
                    return image_links
            except:
                notices.print_note(None, 1, "get_image_links",
                                   "Error retriving image links")
                images.ignore_images = True
                return None
            else:
                return None
        else:
            return None
            # try:
            #     # Try again to connect to the image server
            #     req = requests.get(global_vars.venue_img_dir, timeout=2)
            #     # Connection successul. Unset ignore images
            #     images.ignore_images = False

            #     # TODO return image links for given venue, now that connection to image server is working
            #     return None
            # except:
            #     return None

    def save_places_venue_images(self, image_list, uuid):
        if image_list == None or image_list == []:
            raise DataError(
                notices.print_note(None, 2, "save_places_venue_images",
                                   "Image List is null"))
        try:
            image_num = 0
            for image_obj in image_list:

                if image_num == 5:
                    break

                image_reference = image_obj['photo_reference']
                image_req = requests.get(
                    global_vars.PLACES_PHOTOS_URL, {
                        'maxwidth': 1200,
                        'photoreference': image_reference,
                        'key': global_vars.PLACES_API_KEY
                    })

                # Get image format and check for content-type of 'image'
                content_type = image_req.headers['Content-Type']
                content_type = re.findall(r"(image)\/(.*)", content_type)
                
                try:
                    check_image = content_type[0][0]
                    if (check_image == 'image'):
                        image_format = content_type[0][1]
                    else:
                        raise DataFormat(
                            notices.print_note(
                                None, 2, "save_places_venue_images",
                                "Content type not an 'image' {}".format(
                                    check_image)))
                except DataFormat as e:
                    print(e)

                images.upload_venue_image(None, image_num, uuid,
                                          image_req.content, image_format)

                image_num += 1
            return 'success'
        except:
            return 'save_places_venue_images error. See: {}'.format(
                str(traceback.print_exc()))

    # Uploads an image to the image_handler server
    # Returns the response object
    def upload_venue_image(self, image_number, uuid, image_data, image_format):
        try:
            metadata = {
                "type": "venue",
                "id": uuid,
                "format": image_format,
                "img_num": image_number,
                "overwrite": False,
                "append": True
            }

            req = requests.post(Config.get('images')['api_host']+global_vars.add_image_ep,
                                files={
                                    'meta': json.dumps(metadata),
                                    'img': image_data
                                })
            req = req.json()
            print(req['message'])
            if (req['status'] == 'OK'):
                return req
            else:
                raise Exception

        except:
            traceback.print_exc()


class venue_h_funcs:
    def to_list(self, obj):
        try:
            obj = ast.literal_eval(obj)
        except:
            obj = None
        return obj

    def open_status(self, hours_obj, venue_name=None):
        try:
            if (hours_obj != None):
                open_status = venue_h_funcs.is_venue_open(
                    None, hours_obj, venue_name=venue_name)
            else:
                open_status = None
        except Exception as e:
            notices.print_note(None, 2, "build_venue_info_obj",
                               "Error preparing hours: {}".format(str(e)))
            open_status = None
        return open_status

    # Returns true if current time is within opening hours
    # ! Does not adjust for timezones. All times are assumed to be AEST
    # TODO fix above
    def is_venue_open(self, hours, venue_name=None):
        # venue_name used for debugging
        # 2 formats are accepted. hours_weekday, and hours_raw. Both are lists
        is_open = None
        try:
            if (type(hours) == list):
                # Raw format
                if (type(hours[0]) == dict):
                    # TODO open_now func for "raw_format"
                    pass
                # Is in pretty format
                if (type(hours[0]) == str):
                    # get day of week
                    days = [
                        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                        "Saturday", "Sunday"
                    ]
                    current_day_of_week = days[datetime.today().weekday()]
                    # get the venue hours of the current day
                    for venue_day_hours in hours:
                        if current_day_of_week in venue_day_hours:
                            # Check for "closed" today
                            if 'Closed' in venue_day_hours:
                                return False
                            else:
                                # Get a datetime object for open and close
                                open_close_hours = re.findall(
                                    current_day_of_week + ': (.*) – (.*)',
                                    venue_day_hours)
                                try:
                                    open_time = open_close_hours[0][0]
                                    close_time = open_close_hours[0][1]
                                except:

                                    notices.print_note(
                                        None, 1, "is_venue_open",
                                        "Error regexing opening hours: '{}' \nVenue Name: {}"
                                        .format(str(open_close_hours),
                                                venue_name))
                                    return is_open

                                # Create a datetime object
                                # Open time will always be today
                                try:
                                    open_time_obj = time.strptime(
                                        open_time, "%I:%M %p")
                                    close_time_obj = time.strptime(
                                        close_time, "%I:%M %p")
                                except ValueError:
                                    try:
                                        # TODO Handle incorrectly formatted time i.e. missing 'am', 'pm'
                                        close_time_obj = time.strptime(
                                            close_time, "%I:%M %p")
                                        open_time_obj = time.strptime(
                                            open_time + ' ' + time.strftime(
                                                "%p", close_time_obj),
                                            "%I:%M %p")

                                    except ValueError:
                                        print(
                                            time.strftime(
                                                "%p", close_time_obj))
                                        notices.print_note(
                                            None, 1, "is_venue_open",
                                            "Incorrectly formatted hours: '{}'\nVenue Name: {}"
                                            .format(str(open_time),
                                                    venue_name))
                                        return is_open

                                open_datetime = datetime.combine(
                                    dtdate.today(),
                                    dttime(open_time_obj.tm_hour,
                                           open_time_obj.tm_min))

                                # Close time could be either today or tomorrow
                                # This creates a problem in how to identify if
                                # close time is today or tomorrow
                                #
                                # It will be assumed that if the close time is 'am'
                                # it is referring to the following day. This method
                                # is not perfect, and will mislabel some times incorrectly.

                                # If hour is less than 12, it is 'am'
                                if (close_time_obj.tm_hour < 12):
                                    # create a dt obj with tomorrows date
                                    close_datetime = datetime.combine(
                                        dtdate.today() + timedelta(days=1),
                                        dttime(close_time_obj.tm_hour,
                                               close_time_obj.tm_min))
                                else:
                                    close_datetime = datetime.combine(
                                        dtdate.today(),
                                        dttime(close_time_obj.tm_hour,
                                               close_time_obj.tm_min))

                                current_datetime = datetime.now()

                                # Check if current time is within open range
                                if (open_datetime <= current_datetime <=
                                        close_datetime):

                                    return True
                                else:
                                    return False

        except Exception as e:
            traceback.print_exc()
            notices.print_note(None, 2, "is_venue_open",
                               "Unknown error: {}".format(e))
            return is_open

    # Prettify type string (remove underscores, capitalise)
    def prepare_types(self, types_list):
        formatted_types = []
        for each_type in types_list:
            each_type = each_type[:1].upper() + each_type[1:]
            each_type = each_type.replace("_", " ")
            formatted_types.append(each_type)
        return formatted_types

    # Pretty open status
    def format_open_status(status):
        if status == None:
            status = None
        elif status == False:
            status = 'Closed'
        elif status == True:
            status = "Open Now!"
        return status

    def format_costs_message(is_usually_ticketed):
        message = None
        if (is_usually_ticketed != None):
            if is_usually_ticketed == 1:
                message = "This event and this venue usually has entry costs."

            elif is_usually_ticketed == 0:
                message = "This venue usually has free entry."

        return message


class event_h_funcs:
    # TODO standardise ticket info/text vars properly.
    # Currently the type of price switches from str to int depending on what is called
    def format_price_and_ticket(ticket, price, usual):
        try:
            # Usual is a bool that indicates a venue usually has paid entry/ticket costs
            # Ticket is a bool, with 3 values.
            # 0 = False (definite. if false then the event has been verified to be free)
            # 1 = True
            # None = No information is known about the event
            if (usual != None):

                if ticket == None and usual == 1:
                    ticket_text = "Sorry, we dont have any pricing information for this event."
                    price = None
                    return ticket_text, price
                elif ticket == None and usual == 0:
                    ticket_text = "Sorry, we dont have any pricing information for this event."
                    price = None
                    return ticket_text, price
                elif ticket == 0 and usual == 1:
                    ticket_text = "Free Gig!"
                    price = None
                    return ticket_text, price

            if ticket == None:
                ticket_text = "Sorry, we don't have any pricing information for this event"
                price = None
            elif ticket == 0:
                ticket_text = "Free Gig!"
                price = None
            elif (ticket > 0 and price > 0):
                ticket_text = 'Ticket: '
                price = '$' + str(price)
            else:
                ticket_text = 'Sorry, we dont have anys pricing information for this event'
                price = None
            return ticket_text, price
        except:
            ticket_text = 'Sorry, we dont have anys pricing information for this event'
            price = None

        return ticket_text, price

    def format_fields(event_info):
        try:
            ticket_text, price = event_h_funcs.format_price_and_ticket(
                event_info['event_info']['ticket'],
                event_info['event_info']['price'],
                event_info['venue_info']['costs']['is_usually_ticketed'])

            # Construct ticket obj
            event_info['event_info']['ticket'] = {
                "is_ticketed": event_info['event_info']['ticket'],
                "price": price,
                "text": ticket_text
            }

            # Remove kv pairs
            event_info['event_info'].pop("price")

            return event_info
        except KeyError:
            try:
                if (event_info['price'] is not None
                        and event_info['price'] > 0):
                    price = '$' + str(event_info['price'])
                elif (event_info['ticket'] == False):
                    price = "Free Gig!"
                else:
                    price = None

                # Construct ticket obj
                event_info['ticket'] = {
                    "is_ticketed": event_info['ticket'],
                    "price": price,
                    # "text": ticket_text
                }

                # Remove kv pairs
                event_info.pop("price")

                return event_info
            except Exception as e:
                traceback.print_exc()
                
                notices.print_note(None, 2, "format_fields",
                                   "Unknown error: {}".format(e))

    def check_event_conflict(self, cursor, event_time, event_venue_id, event_date):
        """
            Conflict occurs when events with 2 different titles are at the same venue and the same time.
            Different to a duplicate which is where both titles are the same.
            Returns True if event is conflicting.
        """
        sql = "SELECT 1 FROM `gigs` WHERE `venue_id` = %s AND `time` = %s AND `date` = %s AND `active` = 1"
        val = (
            event_venue_id,
            event_time,
            event_date
        )

        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        if (len(myresult) > 0):
            return True
        else:
            return False

    # ! WIP - Not implemented
    def compare_event_fields(self, cursor, new_event):
        """
            Compares the new event data with current data,
            and updates accordingly.
            
            I.e the current event is a stub and the new event
            has a matched artist. Update the current event 
            artist id with the new.
            Same for description
        """
        print("New event conflict: Event: {}".format(new_event))
        
        # Get current event data
        sql = "SELECT * FROM `gigs` WHERE `venue_id` = %s AND `time` = %s AND `date` = %s"
        val = (
            new_event['venue_id'],
            new_event['time'],
            new_event['date'],
        )

        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        
        if len(myresult) > 1:
            pass
        elif len(myresult) == 0:
            pass

        elif len(myresult) == 1:
            current_event = myresult[0]
            
            # Compare if current is a stub
            # Get the artist info for current event artist id
            current_event_artist_info = artist_h_funcs.get_artist_info_from_id(None, cursor, current_event[1])
            is_current_event_stub = False
            
            new_artist_info = artist_h_funcs.get_artist_info_from_id(None, cursor, new_event['artist_id'])
            is_new_event_stub = new_artist_info[16]
            
            if current_event_artist_info is not None:
                if (current_event_artist_info[16] == 1):
                    is_current_event_stub = True
                
                if is_current_event_stub and is_new_event_stub != True:
                    print("New event is not a stub, old is")
                    # The new event is an artist
                    # Try and replace the current event with the the new artist
                    
                    # However, we check to see if the artist name exists in the 
                    # current event title or the description (this is to double check that
                    # the new event really is the same event as the current)
                    # If the artist name is not present in either the title or desc
                    # theres is a decent chance that the events are actually different
                    # Therefore we ignore this new event and print to log
                    
                    # Normalise text
                    new_event_title = new_artist_info[1].lower().replace(" ", "")
                    current_event_title = current_event_artist_info[1].lower().replace(" ", "")
                    # Event Description
                    if (current_event[15]):
                        current_event_description = current_event[15].lower().replace(" ", "")
                    else:
                        current_event_description = ""
                        
                    if (new_event_title in current_event_title or new_event_title in current_event_description):
                        # Both events are confirmed the same
                        # Update the current event artist with the new
                        notices.print_note(None, 0, "compare_event_fields", "Updating stub event with artist: \nOld: {}, New: {}".format(current_event_artist_info[1] , new_artist_info[1]))
                        event_h_funcs.update_event_title(None, cursor, current_event[1], new_event['artist_id'])
                        
                        # if the current event has no description and the new one does, update description
                        if (current_event_description == "" and new_event['description']):
                            notices.print_note(None, 0, "compare_event_fields", "Updating event description: \nEvent title: {}, Desc: {}".format(new_artist_info[1], new_event['description']))

                            event_h_funcs.update_event_description(None, cursor, current_event[1], new_event['description'])
                else:
                    print('Both events are stubs')

        else:
            pass

    
    def update_event_title(self, cursor, current_event_id, new_artist_id):
        sql = "UPDATE `gigs` SET `artist_id` = %s WHERE `gigs`.`gig_id` = %s"
        val = (
            new_artist_id,
            current_event_id,
        )
        cursor.execute(sql, val)
    
    def update_event_description(self, cursor, current_event_id, new_description):
        sql = "UPDATE `gigs` SET `artist_id` = %s WHERE `gigs`.`description` = %s"
        val = (
            new_description,
            current_event_id,
        )
        cursor.execute(sql, val)

    # TODO refactor this
    def check_event_duplicate(self, cursor, artist_id, venue_id, time, date):
        # Two checks are made. It is common for events that are listed on different sources to have
        # differnt start times. They are usually within 30 mins. Check both befor and after 30 mins for 
        # a duplicate event.
        # A more robust method would be to check every minute +-30 mins.
        # TODO see above
        
        # Removed 'active' so that duplicates are now checked against pending events
        sql = "SELECT 1 FROM `gigs` WHERE `artist_id` = %s AND `venue_id` = %s AND `time` = %s AND `date` = %s" # AND `active` = 1"
        
        val = (
            artist_id,
            venue_id,
            time,
            date
        )
        print(val)
        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        
        if (len(myresult) > 0):
            return True
        else:
            time_delta = int(time) + 30
            val = (
                artist_id,
                venue_id,
                time_delta,
                date
            )
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            if (len(myresult) > 0):
                return True
            else:
                time_delta = int(time) - 30
                val = (
                    artist_id,
                    venue_id,
                    time_delta,
                    date
                )
                cursor.execute(sql, val)
                myresult = cursor.fetchall()
                if (len(myresult) > 0):
                    return True
                else:
                    return False
    
    def disable(self, cursor, event_id):
        sql = "UPDATE `gigs` SET `active` = '0' WHERE `gigs`.`uuid` = %s"
        val = (
            event_id,
        )
    
        cursor.execute(sql, val)
        
        if (cursor.rowcount == 1):
            return True
        else:
            return False
        
    def activate(self, cursor, event_id):
        sql = "UPDATE `gigs` SET `active` = '1' WHERE `gigs`.`uuid` = %s"
        val = (
            event_id,
        )
    
        cursor.execute(sql, val)
        
        if (cursor.rowcount == 1):
            return True
        else:
            return False
    
    def approve(self, cursor, event_id):
        sql = "UPDATE `gigs` SET `pending` = '0', `active` = '1' WHERE `gigs`.`uuid` = %s"
        val = (
            event_id,
        )
    
        cursor.execute(sql, val)
        
        if (cursor.rowcount == 1):
            return True
        else:
            return False
        
    def event_details(self, cursor, event_id):
        base_sql = "SELECT gigs.ticket, gigs.date, gigs.time, gigs.price, gigs.facebook_event_link, gigs.duration, gigs.description, gigs.event_link, gigs.venue_id FROM gigs"
        sql = base_sql + " WHERE gigs.uuid = '{}'".format(event_id)

        try:
            cursor.execute(sql)

            myresult = cursor.fetchall()
            row_headers = [x[0] for x in cursor.description]
            event_info = dict(zip(row_headers, myresult[0]))
            return event_info

        except Exception as e:
            res = {}
            res['status'] = 'ERROR'
            print(e)
            return res

    
class artist_h_funcs:
    def get_artist_info_from_id(self, cursor, artist_id):
        sql = "SELECT * FROM `artists` WHERE `artist_id` = %s"
        val = (
            artist_id,
        )
        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        if (len(myresult) == 1):
            return myresult[0]
        else:
            return None
        
    def is_stub(self, cursor, artist_id):
        sql = "SELECT `temp` FROM `artists` WHERE `uuid` = %s"
        val = (
            artist_id,
        )
        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        if (len(myresult) == 1):
            return myresult[0][0]
        else:
            return None
    
