from ..sql.sql_connector import connector_for_class_method
from ..sql.queries import queries as q

from ..helper_funcs import db_funcs as db
from ..helper_funcs import notices as n
from ..helper_funcs import global_vars as global_vars
from ..helper_funcs import images as img
from ..helper_funcs import response_builder as response_builder
import time
import ast
from aiohttp import web
import requests
import datetime
from datetime import timedelta
import re
import traceback

from .events import upcoming as get_event

class venue_info:
    @connector_for_class_method
    def venue_from_req(self, cursor, request):
        venue_id = request.query['id']
        print(venue_id)
        return venue_info.venue_info(None, cursor, request, venue_id)
    
    def venue_info(self, cursor, request, venue_id):
        stime = time.time()
        res = {}
        sql = "SELECT * FROM `venues` WHERE venues.uuid = '{}'".format(str(venue_id))
        cursor.execute(sql)
        myresult = cursor.fetchall()

        try:
            
            res = myresult[0]
            
            _venue_info = venue_info.build_venue_info_obj(None, cursor, res)
            res = {
                "venue_info": _venue_info,
                "upcoming_events": get_event.upcoming(None, 'venue', res[0], request, cursor)
            }

        except IndexError:
            print("ERROR")
            res = web.Response(body=None, status=204, headers=None, content_type=None, charset=None, zlib_executor=None)
            res = res.prepare(request)

        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
        return res

    # * basic_info was originally created to return a slim version of the info model for efficiency
    # * but has slowly grown to meet front end requirements and has become almost a
    # * duplicate of get_venue_info, minus 'upcoming'
    # Used for web app view event page that requires basic information about a venue
    # Used in the search_region to provide basic venue information...
    # TODO Reconsider search_region venue data requirement
    # TODO Merge get_venue_basic_info with venue_info?
    def get_venue_basic_info(self, cursor, venue_id):
        # stime = time.time()
        _venue_info = {}
        
        sql = "SELECT * FROM `venues` WHERE venues.uuid = '{}'".format(str(venue_id))

        cursor.execute(sql)
        myresult = cursor.fetchall()
        try:
            res = myresult[0]
            _venue_info = venue_info.build_venue_info_obj(None, cursor, res)
        except IndexError:
            print("ERROR at get_venue_basic_info")
        return _venue_info

    # Builds the venue object from the response from the sql query
    def build_venue_info_obj(self, cursor, sql_response):
        # print('Building Venue Obj')
        # stime = time.time()
        if sql_response[18] == 1:
            image_links = img.get_image_links(None, 'venue', sql_response[16])
        else:
            image_links = None


        address_formatted = sql_response[4].replace(', ', ',\n')
        venue_info = {
            "name": sql_response[3],
            "rating": sql_response[9],
            "address": address_formatted,
            "suburb": sql_response[5],
            "hours": venue_h_funcs.to_list(None, sql_response[6]), # * Figure out how to take in 2 options. 1 for hours_raw, and another for hours_formatted
            "price": sql_response[11],
            "socials": {
                "website": sql_response[10],
                "fb_link": sql_response[13]
                },
            "google_place_id": sql_response[14],
            "description": sql_response[15],
            "types": venue_h_funcs.prepare_types(None, db.get_venue_types(None, cursor, sql_response[0])),
            "id": sql_response[16],
            "open_status": venue_h_funcs.open_status(None, venue_h_funcs.to_list(None, sql_response[6]), sql_response[3]),
            "has_img": sql_response[18],
            "img_links": image_links,
            "usually_ticketed": sql_response[22],
            }

        # * Check for image links, and update has_image
        # This is to prevent has_image being true
        # while not delivering links
        if venue_info['has_img']:
            if(venue_info['img_links'] == {} or venue_info['img_links'] == None):
                venue_info['has_img'] = False
        # etime = time.time()
        # print('TIme took: ' + str(((etime - stime) * 1000)))
        return venue_info
    

class venues_list:
    # Returns a very-slim venue object. Used for 'browse' in web app
    # Currently returns all active venues in table
    # TODO implement by region and tag
    @connector_for_class_method
    def venues_all(self, cursor, request):
        # TODO Figure out the best method to track function time. Decorator func, that appends a meta object to a response?
        # stime = time.time()
        tlist = []

        sql = "SELECT `venue_id`, `name`, `suburb`, `price_level`, `has_img`, `hours_weekday`, `hours_raw`, `usually_ticketed`, `uuid` FROM `venues` WHERE venues.active = True"
        cursor.execute(sql)

        stime = time.time()
        myresult = cursor.fetchall()
        etime = time.time()
        print('SQL request took: ' + str(etime - stime))
        try:
            venue_list = []
            tlist = {
                "total": 0,
                "num": 0,
            }
            for line in myresult:
                stime = time.time()
                # TODO implement open status func for raw hours
                # if line[6] == None or line[6] == '':
                #     hours_raw = line[5]
                # else:
                #     hours_raw = line[6]

                hours_raw = line[5]

               
                if line[4] == 1:
                    image_links = img.get_image_links(None, 'venue', line[8])
                else:
                    image_links = None

                prep_types = None
                prep_types = venue_h_funcs.prepare_types(None, db.get_venue_types(None, cursor, line[0]))

                venue_obj = {
                    "name": line[1],
                    "suburb": line[2],
                    "price": line[3],
                    "types": prep_types,
                    "id": line[8],
                    "open_status": venue_h_funcs.open_status(None, venue_h_funcs.to_list(None, hours_raw), venue_name=line[1]),
                    "has_img": line[4],
                    "img_links": image_links,
                    "usually_ticketed": line[7],
                    }

                venue_list.append(venue_obj)

                etime = time.time()
                ttime = etime - stime
                tlist['total'] += ttime
                tlist['num'] += 1
                print('Venue time took: ' + str((ttime)))
            print('Average time per venue took: ' + str((tlist['total']/tlist['num'])*1000) + 'millisecs')

            return response_builder.build_res(None, venue_list, 'venues_list',
                                          request, stime)
        except Exception as e:
            # n.print_note(None, 2, "venues_all", "Unknown error: {}".format(e))
            return n.print_note(None, 2, "venues_all", "Unknown error: {}".format(e))


class venue_h_funcs:
    def to_list(self, obj):
        try:
            obj = ast.literal_eval(obj)
        except:
            obj = None
        return obj

    def open_status(self, hours_obj, venue_name=None):
        try:
            if(hours_obj != None):
                open_status = venue_h_funcs.is_venue_open(None, hours_obj, venue_name=venue_name)
            else:
                open_status = None
        except Exception as e:
            n.print_note(None, 2, "build_venue_info_obj", "Error preparing hours: {}".format(str(e)))
            open_status = None
        return open_status

    # Returns true if current time is within opening hours
    # ! Does not adjust for timezones. All times are assumed to be AEST
    # TODO Adjust for timezone in is_venue_open
    # TODO Move to helper funcs module
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
                if(type(hours[0]) == str):
                    # get day of week
                    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    current_day_of_week = days[datetime.datetime.today().weekday()]
                    # get the venue hours of the current day
                    for venue_day_hours in hours:
                        if current_day_of_week in venue_day_hours:
                            # Check for "closed" today
                            if 'Closed' in venue_day_hours:
                                return False
                            else:
                                # Get a datetime object for open and close
                                open_close_hours = re.findall(current_day_of_week+': (.*) – (.*)', venue_day_hours)
                                try:
                                    open_time = open_close_hours[0][0]
                                    close_time = open_close_hours[0][1]
                                except:
                                    
                                    n.print_note(None, 1, "is_venue_open", "Error regexing opening hours: '{}' \nVenue Name: {}".format(str(open_close_hours), venue_name))
                                    return is_open

                                # Create a datetime object
                                # Open time will always be today
                                try:
                                    open_time_obj = time.strptime(open_time, "%I:%M %p")
                                    close_time_obj = time.strptime(close_time, "%I:%M %p")
                                except ValueError:
                                    try:
                                        # TODO Handle incorrectly formatted time i.e. missing 'am', 'pm'
                                        close_time_obj = time.strptime(close_time, "%I:%M %p")
                                        open_time_obj = time.strptime(open_time + ' ' + time.strftime("%p", close_time_obj), "%I:%M %p")

                                    except ValueError:
                                        print(time.strftime("%p", close_time_obj))
                                        n.print_note(None, 1, "is_venue_open", "Incorrectly formatted hours: '{}'\nVenue Name: {}".format(str(open_time), venue_name))
                                        return is_open

                                open_datetime = datetime.datetime.combine(datetime.date.today(), datetime.time(open_time_obj.tm_hour, open_time_obj.tm_min))

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
                                    close_datetime = datetime.datetime.combine(datetime.date.today()+timedelta(days=1), datetime.time(close_time_obj.tm_hour, close_time_obj.tm_min))
                                else:
                                    close_datetime = datetime.datetime.combine(datetime.date.today(), datetime.time(close_time_obj.tm_hour, close_time_obj.tm_min))

                                current_datetime = datetime.datetime.now()

                                # Check if current time is within open range
                                if (open_datetime <= current_datetime <= close_datetime):

                                    return True
                                else:
                                    return False

                

        except Exception as e:
            traceback.print_exc()
            n.print_note(None, 2, "is_venue_open", "Unknown error: {}".format(e))
            return is_open

    # Prettify type string (remove underscores, capitalise)
    def prepare_types(self, types_list):
        formatted_types = []
        for each_type in types_list:
            # if (each_type != "locality"):
            #     each_type = each_type[:1].upper() + each_type[1:]
            #     if '_' in each_type:
            #         each_type.replace("_", " ")
                
            #     formatted_types.append(each_type)
            each_type = each_type[:1].upper() + each_type[1:]
            each_type = each_type.replace("_", " ")
                
            formatted_types.append(each_type)
        return formatted_types

