from ..sql.sql_connector import connector_for_class_method

from ..helper_funcs import db_funcs as db
from ..helper_funcs import notices as n
from ..helper_funcs import global_vars as global_vars
from ..helper_funcs import images as img
from ..helper_funcs import response_builder as response_builder
from ..helper_funcs import venue_h_funcs as venue_h_funcs
import time
from aiohttp import web


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
    # * but has slowly grown to satisfy front end requirements and has become almost a
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
        if sql_response[17] == 1:
            image_links = img.get_image_links(None, 'venue', sql_response[15])
        else:
            image_links = None


        address_formatted = sql_response[3].replace(', ', ',\n')
        venue_info = {
            "name": sql_response[2],
            "rating": sql_response[8],
            "address": address_formatted,
            "suburb": sql_response[4],
            "hours": venue_h_funcs.to_list(None, sql_response[5]), # * Figure out how to accept 2 options. 1 for hours_raw, and another for hours_formatted
            "price": sql_response[10],
            "socials": {
                "website": sql_response[9],
                "fb_link": sql_response[12]
                },
            "google_place_id": sql_response[13],
            "description": sql_response[14],
            "types": venue_h_funcs.prepare_types(None, db.get_venue_types(None, cursor, sql_response[0])),
            "id": sql_response[15],
            "open_status": venue_h_funcs.format_open_status(venue_h_funcs.open_status(None, venue_h_funcs.to_list(None, sql_response[5]), sql_response[2])),
            "has_img": sql_response[17],
            "img_links": image_links,
            "costs": {
                "is_usually_ticketed": sql_response[21],
                "text": venue_h_funcs.format_costs_message(sql_response[21])
            }
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


