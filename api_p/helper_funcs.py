import re
import time
import traceback
import json
from datetime import datetime
from datetime import timedelta
# from .sql.config import config as config 
import requests
from .exceptions import *
from uuid import UUID
import inspect

# Testing. Ignore this
REQUEST_NUM = 0

import socket
def logger(text):
    HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
    PORT = 12123        # Port to listen on (non-privileged ports are > 1023)
    # run = True

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    with server as s:
        # try:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        try:
            data = text.encode('ascii')
            # while i < 1000:
            conn.sendall(data)
                # print('Sending')
                # i +=1
            conn.close()
            s.shutdown(socket.SHUT_RDWR)
            s.close()

        except BrokenPipeError:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            pass
        except ConnectionResetError:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            pass
        except KeyboardInterrupt:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            # run = False


def print_req_info(func):
    def wrapper(request, *args, **kwargs):
        global REQUEST_NUM
        REQUEST_NUM += 1
        stime = time.time()
        print("======== Begin Request ========")
        print("Server time: {}".format(
            datetime.now().strftime("%H:%M:%S.%f")))
        print("Request: {}".format(request.path))
        print("Global Req. number: ", REQUEST_NUM)
        print("Client: " + request.host)
        print("Origin IP: " + request.remote)
        func(request, *args, **kwargs)
        etime = time.time()
        print("Time to complete: " + str((etime - stime)*1000) + " ms")
        print("========= End Request =========")
        return 
    return wrapper


class h_funcs:
    # Print information about each request in terminal
    def print_req_info(self, request):
        # Add time delay
        # time.sleep(2)
        global REQUEST_NUM
        global changed
        REQUEST_NUM += 1
        print("======== Begin Request ========")
        print("Server time: {}".format(
            datetime.now().strftime("%H:%M:%S.%f")))
        print("Request: {}".format(request.path))
        print("Global Req. number: ", REQUEST_NUM)
        print("Client: " + request.host)
        print("Origin IP: " + request.remote)
        # print("========= End Request =========")
        text = """======== Begin Request ========
Server time: {}
Request: {}
Global Req. number: {}
Client: {}
Origin IP: {}
========= End Request =========""".format(datetime.now().strftime("%H:%M:%S.%f"), request.path, REQUEST_NUM, request.host, request.remote)
        # logger(text)
        # print('Log buffer is : ' + LOG_BUFFER)

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



class db_funcs():
    # TODO implement success responses/error handling for helper funcs
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

    def get_source_id(self, cursor, src_name):
        table = "sources"
        column = "name"

        # Plan was to originally have a many sources (websites) for data gathering
        # this would have required the ability to create new sources on the fly.
        # Plan has changed to be mostly manual input.
        if not db_funcs.check_exist(None, cursor, table, column, src_name):
            sql = "INSERT INTO `sources` (name) VALUES (%s);"
            val = (
                src_name,
            )
            cursor.execute(sql, val)
            source_id = cursor.lastrowid
        else:
            sql = "SELECT * FROM `sources` WHERE `name` = %s"
            val = (src_name,)
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            source_id = myresult[0][0]
        return source_id

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
            raise UUIDNotFound(notices.print_note(None, 2, "get_id_from_uuid",
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
                sql = "SELECT `uuid` FROM `venues` WHERE `venue_id` = '{}'".format(_id)
                cursor.execute(sql)
                myresult = cursor.fetchall()
                return myresult[0][0]
            else:
                raise IDNotFound(notices.print_note(None, 2, "get_uuid_from_id",
                               "No artist or venue with id: {}".format(_id)))
        return notices.print_note(None, 2, "get_uuid_from_id",
                               "Id is None")

    # Returns an internal id based off a name only match
    # Used in the post_event handler func. This must be deprecated in near future
    # because of high chances of name duplicates with a larger dataset.
    # Only used for MVP development.
    def get_id_from_name(self, cursor, _type, name):
        if (_type == 'venue'):
            sql = "SELECT `venue_id` FROM `venues` WHERE `name` = %s"
            val = (name,)
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            if (len(myresult) > 1):
                notices.print_note(
                    None, 2, "get_id_from_name",
                    "More than 1 record with name: {}".format(name))
                raise MoreThanOneRecordReturned(notices.print_note(
                    None, 2, "get_id_from_name",
                    "More than 1 record with name: {}".format(name)))
            elif (len(myresult) == 1):
                return myresult[0][0]
            else:
                raise IDNotFound(notices.print_note(None, 2, "get_id_from_name",
                                   "No venue with name: {}".format(name)))

        elif (_type == 'artist'):
            sql = "SELECT `artist_id` FROM `artists` WHERE `name` = %s"
            val = (name,)
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            if (len(myresult) > 1):
                raise MoreThanOneRecordReturned(notices.print_note(
                    None, 2, "get_id_from_name",
                    "More than 1 record with name: {}".format(name)))
            elif (len(myresult) == 1):
                return myresult[0][0]
            else:
                
                raise RecordNotFound(notices.print_note(None, 2, "get_id_from_name",
                                   "No artist with name: {}".format(name)))
        else:
            raise CategoryError(notices.print_note(
                None, 2, "get_id_from_name",
                "Type must be 'artist' or 'venue', given: {}".format(_type)))

    def check_gig_exists_with_uuid(self, cursor, artist_id, venue_id, time):
        sql = "SELECT 1 FROM `gigs` WHERE artists.uuid = %s AND venues.uuid = %s AND `time` = %s"
        val = (
            artist_id,
            venue_id,
            time,
        )
        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        return myresult
    
    def check_gig_exists_with_id(self, cursor, artist_id, venue_id, time):
        sql = "SELECT 1 FROM `gigs` WHERE `artist_id` = %s AND `venue_id` = %s AND `time` = %s"
        val = (
            artist_id,
            venue_id,
            time,
        )
        cursor.execute(sql, val)
        myresult = cursor.fetchall()
        if(len(myresult) > 0):
            return True
        else:
            return False
        

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

    def insert_event(self, cursor, event_info):
        try:
            if (type(event_info) != dict):
                notices.print_note(
                    None, 2, "insert_event",
                    "event_info must be dict: given {}".format(type(event_info)))
                raise Exception

            elif(db_funcs.check_gig_exists_with_id(None, cursor, event_info['artist_id'], event_info['venue_id'], event_info['time'])):
                raise Duplicate( notices.print_note(
                    None, 0, "insert_event",
                    "Event already exists: {}".format(str(event_info))))
            else:
                try:
                    sql = "INSERT INTO `gigs`(`artist_id`, `venue_id`, `user_id`, `source_id`, `ticket`, `date`, `time`, `price`, `facebook_event_link`, `uuid`, `duration`, `description`, `event_link`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, UUID(), %s, %s, %s)"
                    vals = (
                        event_info['artist_id'],
                        event_info['venue_id'],
                        event_info['user_id'],
                        event_info['source_id'],
                        event_info['ticket'],
                        event_info['date'],
                        event_info['time'],
                        event_info['price'],
                        event_info['facebook_event_link'],
                        event_info['duration'],
                        event_info['description'],
                        event_info['event_link']
                    )
                    cursor.execute(sql, vals)
                    res = {
                        "status": "OK",
                        "message": "Succesfully created new event"
                    }
                    return res
                    
                except Exception as e:
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
        if type(list_obj) is dict :
            for each in list_obj:
                num += len(list_obj[each])
        elif type(list_obj) is list:
            num += len(list_obj)
        

        meta_data = {
            "rqst": request.path,
            "time_rcvd": stime,
            "time_sent": time.time(),
            "time_total": str((time.time() - stime)*1000) + ' ms',
            "num_of_obj": num,
            
        }

        # Update metada with custom fields
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

from .sql.config import config

# TODO move to config file
class global_vars:
    img_server = config.image_config['host']
    img_handler = img_server+"/handler"
    add_image_ep = img_handler + '/image'
    img_dir = '/assets/img/'
    venue_img_dir = img_server + img_dir + 'venues/'
    artist_img_dir = img_server + img_dir + 'artists/'

    PLACES_API_KEY = "AIzaSyDPgUfyiWPK76IytvsJ6-hfmEPOpl6NOLg"
    PLACES_PHOTOS_URL = "https://maps.googleapis.com/maps/api/place/photo"
    PLACES_DETAILS_BASE = "https://maps.googleapis.com/maps/api/place/details/json"


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
                url = global_vars.venue_img_dir + uuid
            elif (artist_or_ven == 'artist'):
                url = global_vars.artist_img_dir + uuid
            try:
                req = requests.get(url, timeout=2)
                if (req.status_code == 200):
                    ex = r"href=\"("
                    ex1 = r"\d*\..*)\""
                    reg_patt = ex + ex1
                    # print(ex2)
                    # print(req.text)
                    matches = re.findall(reg_patt, req.text)
                    # print(matches)
                    for each_match in matches:
                        if (each_match[2] == 0):
                            image_links[0] = url + '/' + each_match
                        else:
                            image_links[len(image_links)] = url + '/' + each_match
                    return image_links
            except:
                notices.print_note(None, 1, "get_image_links", "Error retriving image links")
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
        if (image_list == None or image_list == []):
            raise DataError(notices.print_note(None, 2, "save_places_venue_images", "Image List is null"))
        try:
            image_num = 0
            for image_obj in image_list:
                if image_num == 5:
                    break
                image_reference = image_obj['photo_reference']
                image_req = requests.get(global_vars.PLACES_PHOTOS_URL, {'maxwidth':1200,'photoreference': image_reference, 'key': global_vars.PLACES_API_KEY})
                
                # Get image format and check for content-type of 'image'
                content_type = image_req.headers['Content-Type']
                # print(content_type)
                content_type = re.findall(r"(image)\/(.*)", content_type)
                try:
                    check_image = content_type[0][0]
                    if (check_image == 'image'):
                        image_format = content_type[0][1]
                    else:
                        raise DataFormat(notices.print_note(None, 2, "save_places_venue_images", "Content type not an 'image' {}".format(check_image)))
                except DataFormat as e:
                    print(e)
                    
                images.upload_venue_image(None, image_num, uuid, image_req.content, image_format)

                image_num +=1
            return 'success'
        except:
            return 'save_places_venue_images error. See: {}'.format(str(traceback.print_exc()))
            
    # Uploads an image to the image_handler server
    # Returns the response object
    def upload_venue_image(self, image_number, uuid, image_data, image_format):
        try:
            metadata = {"type": "venue",
                "id": uuid,
                "format": image_format,
                "img_num": image_number,
                "overwrite": False, 
                "append": True
                }


            req = requests.post(global_vars.add_image_ep, files={'meta': json.dumps(metadata), 'img': image_data})
            req = req.json()
            print(req['message'])
            if (req['status'] == 'OK'):
                return req
            else:
                raise Exception

        except:
            traceback.print_exc()
