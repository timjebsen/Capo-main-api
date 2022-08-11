from datetime import datetime as dt
import time
from itertools import groupby
from ..helper_funcs import db_funcs as db
from ..helper_funcs import response_builder as response_builder
from .events import upcoming as upcoming
from .venue import venue_h_funcs as venue_h_funcs
import re
from ..sql.sql_connector import connector_for_class_method


class indexes:
    @connector_for_class_method
    def all(self, cursor):
        stime = time.time()

        # ! DO NOT CHANGE ORDER OF THESE SQL QUERIES
        # ! THE ORDER DICTATES THE 'dbtbl' ID
        # ! THIS IS USED IN THE SEARCH RESPONSE LABELS
        sql_list = [
            "SELECT `uuid`, `name` FROM `artists` WHERE `active` = True",
            "SELECT `uuid`, `name` FROM `venues` WHERE `active` = True",
            "SELECT `uuid`, `genre` FROM `genres`",
            "SELECT `uuid`, `region` FROM `region_polygons`"
        ]

        search_index_list = []
        i = 0
        for query in sql_list:
            cursor.execute(query)
            myresult = cursor.fetchall()
            for each_row in myresult:
                item = {"dbid": each_row[0], "dbtbl": i, "text": each_row[1]}
                search_index_list.append(item)

            i += 1

        etime = time.time()

        print("Time: " + str((etime - stime) * 1000) + " ms")

        return search_index_list

    @connector_for_class_method
    def locations(self, cursor):

        stime = time.time()

        sql_list = "SELECT `venue_id`, `uuid`, `name`, ST_AsText(ST_PointFromWKB(`coordinate`)) FROM `venues`"

        locations_index_list = []

        cursor.execute(sql_list)
        myresult = cursor.fetchall()

        for each_row in myresult:

            coords = re.findall(r"POINT\((.*) (.*)\)", each_row[3])
            lat = float(coords[0][1])
            lng = float(coords[0][0])
            if (lat == 0 or lng == 0):
                print('Venue: {} has 0, 0 coords.'.format(each_row[2]))
            else:
                item = {
                    'name':
                    each_row[2],
                    'uuid':
                    each_row[1],
                    'coords': {
                        'lat': lat,
                        'lng': lng
                    },
                    'events':
                    upcoming.num_upcoming(None, cursor, 'venue', each_row[0]),
                    'venue_type':
                    venue_h_funcs.prepare_types(
                        None, db.get_venue_types(None, cursor, each_row[0]))
                }
                locations_index_list.append(item)

        etime = time.time()

        print("Time: " + str((etime - stime) * 1000) + " ms")

        return locations_index_list

    @connector_for_class_method
    def artists(self, cursor, request):
        stime = time.time()
        sql = "SELECT `name`, `uuid`, `reg_id` FROM `artists` WHERE `active` = True"
        artist_list = []
        cursor.execute(sql)
        myresult = cursor.fetchall()
        if (myresult != None):
            for each in myresult:
                artist = {}
                artist['name'] = each[0]
                artist['id'] = each[1]
                artist['location'] = db.get_region(None, cursor, each[2])
                artist_list.append(artist)

        return response_builder.build_res(None, artist_list, 'artist_list',
                                          request, stime)

    @connector_for_class_method
    def venues(self, cursor, request):
        stime = time.time()
        sql = "SELECT `name`, `uuid` FROM `venues` WHERE `active` = True"
        venues_list = []
        cursor.execute(sql)
        myresult = cursor.fetchall()
        if (myresult != None):
            for each in myresult:
                venue = {}
                venue['name'] = each[0]
                venue['id'] = each[1]
                venues_list.append(venue)

        return response_builder.build_res(None, venues_list, 'venues_list',
                                          request, stime)

    @connector_for_class_method
    def artist_regions(self, cursor, request):
        stime = time.time()
        sql = "SELECT `region`, `state_abr`, `reg_id` FROM `regions`"
        regions_list = []
        cursor.execute(sql)
        myresult = cursor.fetchall()
        if (myresult != None):
            for each in myresult:
                region_obj = {}
                region_obj['region'] = each[0]
                region_obj['state'] = each[1]
                region_obj['id'] = each[2] # * Returns internal id, too lazy to replace with uuid's
                regions_list.append(region_obj)

        return response_builder.build_res(None, regions_list, 'regions_list',
                                          request, stime)

    @connector_for_class_method
    def artist_genres(self, cursor, request):
        stime = time.time()
        sql = "SELECT `genre`, `uuid` FROM `genres`"
        genres_list = []
        cursor.execute(sql)
        myresult = cursor.fetchall()
        if (myresult != None):
            for each in myresult:
                genre_obj = {}
                genre_obj['genre'] = each[0]
                genre_obj['id'] = each[1]
                genres_list.append(genre_obj)

        return response_builder.build_res(None, genres_list, 'genres_list',
                                          request, stime)