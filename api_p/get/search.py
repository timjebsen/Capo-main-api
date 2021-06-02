from datetime import datetime as dt 

import time
from itertools import groupby
from ..sql.sql_connector import connector_for_class_method

from ..helper_funcs import response_builder as response_builder
from .events import upcoming as upcoming
from .venue import venue_info as venue


class search:
    # TODO Crate a table to index venues with matching geo polygons.
    #  ! Current query times are ~500ms even with limited data sets.
    @connector_for_class_method
    def by_region(self, cursor, request):
        # Get all venues in the selected region
        # then check for a gig for each venue
        stime = time.time()
        res = {}
        region_id = request.query['id']

        # Get polygon data for requested region
        sql_set_reg = "SET @g1 = (SELECT `polygon` FROM `region_polygons` WHERE `uuid` = '{}');".format(region_id)
        sql_query = "SELECT venues.venue_id, venues.uuid FROM venues WHERE ST_CONTAINS(@g1, venues.coordinate) AND venues.active = True"
        cursor.execute(sql_set_reg)
        cursor.execute(sql_query)
        result_list = cursor.fetchall()
        
        try:
            event_list_final = {}
            venue_list = []
            for each_venue in result_list:
                # Match associated events with venue
                # get events then append to a gig list
                venue_id = each_venue[0]
                venue_uuid = each_venue[1]
                upcoming_gigs = upcoming.upcoming(None, 'venue', venue_id, request, cursor)
                event_list_temp = upcoming_gigs['gig_list']

                # If a date already exists. Add the currently selected events to it
                # otherwise create new date
                for key in event_list_temp:
                    if (key in event_list_final):
                        # event_list_final[key] = [{event}, {event}...]
                        event_list_final[key].extend(event_list_temp[key])
                        # print('List extended at: {}'.format(key))
                    else:
                        event_list_final[key] = event_list_temp[key]
                
                # Get venue info and add to venue list
                venue_info = venue.get_venue_basic_info(None, cursor, venue_uuid)
                if venue_info != {}:
                    venue_list.append(venue_info)

            gig_list = {}
            gig_list['gig_list'] = event_list_final
            gig_list['meta'] = response_builder.build_meta(None, event_list_final, 1)

            sql = "SELECT `region` FROM `region_polygons` WHERE `uuid` = '{}'".format(region_id)
            cursor.execute(sql)
            region_name = cursor.fetchall()[0][0]

            # Build the locations obj. Used for filtering results
            locations = {
                "suburbs": [
                #     {
                #     "name": "",
                #     "name_raw": "",
                # }
                ]

            }
            for each_venue in venue_list:
                current_venue_suburb = each_venue['suburb']
                raw_name = each_venue['suburb'].lower()
                raw_name = raw_name.replace(' ', '_')
                each_venue['suburb_raw'] = raw_name
                # Iterate over locations suburbs
                #  Eand check for existence
                
                if len(locations['suburbs']) > 0:

                    suburb_exists = False
                    for suburb_obj in locations['suburbs']:
                        if current_venue_suburb == suburb_obj['name']:
                            
                            suburb_exists = True
                            break
                            
                        else:
                            suburb_exists = False

                    if not suburb_exists:
                        new_sub_obj = {}
                        new_sub_obj['name'] = each_venue['suburb']

                        raw_name = each_venue['suburb'].lower()
                        raw_name = raw_name.replace(' ', '_')

                        new_sub_obj['name_raw'] = raw_name

                        locations['suburbs'].append(new_sub_obj)
                else:
                    print('Beginning of suburb list')
                    new_sub_obj = {}
                    new_sub_obj['name'] = each_venue['suburb']

                    raw_name = each_venue['suburb'].lower()
                    raw_name = raw_name.replace(' ', '_')

                    new_sub_obj['name_raw'] = raw_name

                    locations['suburbs'].append(new_sub_obj)

            def get_sub(obj):
                return obj.get('name')

            locations['suburbs'].sort(key=get_sub)

            res = {
                "upcoming_events": gig_list, 
                "venues_list": venue_list,
                "meta": { "region": region_name, 
                "request": request.path},
                "locations": locations
            }

        except KeyError:
            print('no record in polygons with id')

        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
        return res
