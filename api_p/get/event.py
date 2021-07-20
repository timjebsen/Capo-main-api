import time
from datetime import datetime as dt
import datetime
from traceback import print_exc
from ..sql.sql_connector import connector_for_class_method as connector_for_class_method
from ..helper_funcs import artist_h_funcs, db_funcs as db, event_h_funcs
from ..helper_funcs import venue_h_funcs as venue_h_funcs
from itertools import groupby
from ..helper_funcs import response_builder as response_builder
from .venue import venue_info as venue_info
from .artist import artist_info as artist_info
from ..exceptions import *


class gig_info:
    # Return information about an event (artist, venue, and event)
    @connector_for_class_method
    def info(self, cursor, request):
        stime = time.time()

        event_id = request.query['id']
        res = {}

        # get venue uuid and artist uuid asscoaited with the event
        base_sql = "SELECT artists.uuid, venues.uuid \
            FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) \
            INNER JOIN venues ON gigs.venue_id = venues.venue_id)"
        sql = base_sql + " WHERE gigs.uuid = '{}'".format(event_id)

        cursor.execute(sql)
        myresult = cursor.fetchall()

        try:
            if len(myresult) != 0:
                artist_id = myresult[0][0]
                venue_id = myresult[0][1]
                
                event_info = {
                    "event_info": gig_info.event_details(None, cursor, event_id),
                    "venue_info": venue_info.get_venue_basic_info(None, cursor, venue_id),
                    "artist_info": artist_info.artist_info_basic(None, cursor, artist_id),
                    "Status": "OK"
                }
                
                # Re-structure and format fields
                event_info = event_h_funcs.format_fields(event_info)
                
                
                res = event_info
            else:
                raise UUIDNotFound()
        
        except UUIDNotFound:
            return UUIDNotFound.res

        except Exception as e:
            return UnknownError.res

        etime = time.time()
        
        print("Time: " + str((etime - stime)*1000) + " ms")

        return res
    
    def event_details(self, cursor, event_id):
        base_sql = "SELECT gigs.ticket, gigs.date, gigs.time, gigs.price, gigs.facebook_event_link, gigs.duration, gigs.description, gigs.event_link FROM gigs"
        sql = base_sql + " WHERE gigs.uuid = '{}'".format(event_id)
        try:
            row_headers = [x[0] for x in cursor.description]
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


class events_list:
    base_sql = "SELECT artists.name, venues.name, gigs.uuid, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.uuid, venues.uuid, venues.usually_ticketed, venues.hours_weekday \
            FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) \
            INNER JOIN venues ON gigs.venue_id = venues.venue_id)"

    # TODO see below
    @connector_for_class_method
    def day(self, cursor, request):
        stime = time.time()
    
        # If a region is given, only events in venues that exist within the region are added to the events list.
        # When the events list being built, only the events hosted at an 'approved' venue should be added.
        
        # * The current state of filtering events by region is expensive and has many areas that need optimsation.
        # * Replace region queries with indexes (venues and associated regions)
        # * Index of events and which regions they are associated with, 
        # * note, that would require an extra method when a new event is created, and also when a new
        # * region is created a trigger needs to be implemented to rebuild/update the index.
        # TODO see above
        region_venues_list = None
        try:
            region_id = request.query['region']
            
            sql_set_reg = "SET @g1 = (SELECT `polygon` FROM `region_polygons` WHERE `uuid` = '{}');".format(region_id)
            sql_query = "SELECT venues.venue_id, venues.uuid FROM venues WHERE ST_CONTAINS(@g1, venues.coordinate) AND venues.active = True"
            cursor.execute(sql_set_reg)
            cursor.execute(sql_query)
            
            # List of all venues within region
            region_venues_list = cursor.fetchall()

        except KeyError:
            region_id = None
            pass
        except Exception as e:
            print_exc()
        
        
        day = request.query['day']
        plus_day = 0
        if (day == 'today'):
            plus_day = 0
        elif (day == 'tomorrow'):
            plus_day = 1

        plus_day_dt = (dt.today() + datetime.timedelta(days=plus_day))
        date_tomorrow = plus_day_dt.strftime("%Y") + "-" + plus_day_dt.strftime("%m") + \
            "-" + plus_day_dt.strftime("%d")

        sql_mod = " WHERE `date`='{}' ".format(date_tomorrow)
        sql_only_active = "AND artists.active = True AND venues.active = True AND gigs.active = True"
        sql = events_list.base_sql + sql_mod + sql_only_active

        cursor.execute(sql)
        
        row_headers = [x[0] for x in cursor.description]
        row_headers[0] = "artist_name"
        row_headers[1] = "venue_name"
        row_headers[2] = "event_id"
        row_headers[9] = "artist_id"
        row_headers[10] = "venue_id"
        
        myresult = cursor.fetchall()

        gigs = []
        gigs_group = {}
        if (len(myresult) > 0):
            
            for result in myresult:
                event = dict(zip(row_headers, result))
                
                # Re-structure and format fields
                event['genre'] = db.get_genre(None, cursor, result[9])
                event['open_status'] = venue_h_funcs.open_status(None, venue_h_funcs.to_list(None, result[12]), result[1])
                event = event_h_funcs.format_fields(event)
                
                # If a region is given, compare the current event-venue with the list of region_venues_list
                if region_venues_list is not None:
                    # Iterate through the venues list
                    for venue in region_venues_list:
                        if venue[1] == event['venue_id']:
                            gigs.append(event)
                        
                else:
                    gigs.append(event)

            # Sort each event by start time
            gigs.sort(key=lambda gigsg: gigsg['time'])
            
            # Create an iterable where the events are grouped by time
            gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['time'])

            # Restruct the events in groups with the event time as keys
            for t, g in gigs_grouped_iter:
                gigs_group[t] = []
                for e in g:
                    gigs_group[t].append(e)
        else:
            # No gigs today. Return empty
            gigs_group = {}

        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
            # time.sleep(5)
        meta = {}
        meta['group_mode'] = 0
        if len(gigs_group) == 0:
            meta['gigs_today'] = False
        else:
            meta['gigs_today'] = True
        # print("connection after "+str(db_conn.open))
        return response_builder.build_res(None, gigs_group, "events", request, stime, meta)


    # TODO refactor to accept 'day' params
    # TODO include venue is open in event
    @connector_for_class_method
    def month(self, cursor, request):

        stime = time.time()
        
        # Region filter
        region_venues_list = None
        try:
            region_id = request.query['region']
            
            sql_set_reg = "SET @g1 = (SELECT `polygon` FROM `region_polygons` WHERE `uuid` = '{}');".format(region_id)
            sql_query = "SELECT venues.venue_id, venues.uuid FROM venues WHERE ST_CONTAINS(@g1, venues.coordinate) AND venues.active = True"
            cursor.execute(sql_set_reg)
            cursor.execute(sql_query)
            
            # List of all venues within region
            region_venues_list = cursor.fetchall()

        except KeyError:
            region_id = None
            pass
        except Exception as e:
            print_exc()
        
        # * Start day is 2 days from current. This skips the today and tomorrow responses
        start_day_dt = (dt.today() + datetime.timedelta(days=2))
        end_day_dt = (dt.today() + datetime.timedelta(days=30))
        date_start = start_day_dt.strftime("%Y") + "-" + start_day_dt.strftime("%m") + \
            "-" + start_day_dt.strftime("%d")
        date_end = end_day_dt.strftime("%Y") + "-" + end_day_dt.strftime("%m") + \
            "-" + end_day_dt.strftime("%d")

        sql_mod = "WHERE `date` BETWEEN  '{}' AND '{}' ".format(date_start, date_end)
        sql_only_active = "AND artists.active = True AND venues.active = True AND gigs.active = True"
        sql = events_list.base_sql + sql_mod + sql_only_active
        cursor.execute(sql)
        
        row_headers = [x[0] for x in cursor.description]
        row_headers[0] = "artist_name"
        row_headers[1] = "venue_name"
        row_headers[2] = "event_id"
        row_headers[9] = "artist_id"
        row_headers[10] = "venue_id"

        myresult = cursor.fetchall()
        events = []
        events_grouped = {}
        if (len(myresult) > 0):
            for result in myresult:

                event_info = dict(zip(row_headers, result))
                
                # Re-structure and format fields
                event_info['genre'] = db.get_genre(None, cursor, result[9])
                event_info.pop('hours_weekday', None)
                event_info = event_h_funcs.format_fields(event_info)
                event_info['open_status'] = venue_h_funcs.open_status(None, venue_h_funcs.to_list(None, result[12]), result[1])
                # If a region is given, compare the current event-venue with the list of region_venues_list
                if region_venues_list is not None:
                    # Iterate through the venues list
                    for venue in region_venues_list:
                        if venue[1] == event_info['venue_id']:
                            events.append(event_info)
                        
                else:
                    events.append(event_info)
                
            events.sort(key=lambda eventsgrouped: eventsgrouped['time'])

            events_grouped_iter = groupby(events, lambda eventsgrouped: eventsgrouped['date'])

            for w, g in events_grouped_iter:
                try:
                    events_grouped[str(w)]
                except KeyError:
                    events_grouped[str(w)] = []

                for e in g:
                    events_grouped[str(w)].append(e)
            
        
        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
        return response_builder.build_res(None, events_grouped, "events", request, stime, {})
    
    @connector_for_class_method
    def all(self, cursor, request):

        stime = time.time()
        
        # # Region filter
        # region_venues_list = None
        # try:
        #     region_id = request.query['region']
            
        #     sql_set_reg = "SET @g1 = (SELECT `polygon` FROM `region_polygons` WHERE `uuid` = '{}');".format(region_id)
        #     sql_query = "SELECT venues.venue_id, venues.uuid FROM venues WHERE ST_CONTAINS(@g1, venues.coordinate) AND venues.active = True"
        #     cursor.execute(sql_set_reg)
        #     cursor.execute(sql_query)
            
        #     # List of all venues within region
        #     region_venues_list = cursor.fetchall()

        # except KeyError:
        #     region_id = None
        #     pass
        # except Exception as e:
        #     print_exc()
        base_sql = "SELECT artists.name, venues.name, gigs.uuid, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.uuid, venues.uuid, venues.usually_ticketed, venues.hours_weekday, gigs.description, gigs.event_link, gigs.source_id, gigs.user_id, gigs.active, gigs.pending, gigs.date_added \
            FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) \
            INNER JOIN venues ON gigs.venue_id = venues.venue_id)"
        
        start_day_dt = (dt.today())

        date_start = start_day_dt.strftime("%Y") + "-" + start_day_dt.strftime("%m") + \
            "-" + start_day_dt.strftime("%d")

        sql_mod = "WHERE `date` >= '{}'".format(date_start)
        sql_only_active = "AND artists.active = True AND venues.active = True"
        
        sql = base_sql + sql_mod + sql_only_active
        cursor.execute(sql)
        
        row_headers = [x[0] for x in cursor.description]
        row_headers[0] = "artist_name"
        row_headers[1] = "venue_name"
        row_headers[2] = "event_id"
        row_headers[9] = "artist_id"
        row_headers[10] = "venue_id"

        myresult = cursor.fetchall()
        events = []
        events_grouped = {}
        if (len(myresult) > 0):
            for result in myresult:

                event_info = dict(zip(row_headers, result))

                event_info['notes'] = ""
                event_info['level'] = 0
                
                # if stub
                if (artist_h_funcs.is_stub(None, cursor, result[9])):
                    event_info['level'] += 1
                    event_info['notes'] += "Is Stub"
                    
                
                # no description
                if (not result[13]):
                    event_info['level'] += 1
                    event_info['notes'] += " : Desc"
                
                # no event links
                if (not result[14] and not result[7]):
                    event_info['level'] += 1
                    event_info['notes'] += " : Links"
                
                # Get data source
                event_info['source'] = {}
                event_info['source']['name'] = db.get_source_name(None, cursor, result[15])
                event_info['source']['user'] = db.get_name_of_user(None, cursor, result[16])
                    
                events.append(event_info)                
                
                # Re-structure and format fields
                # event_info['genre'] = db.get_genre(None, cursor, result[9])
                # event_info.pop('hours_weekday', None)
                # event_info = event_h_funcs.format_fields(event_info)
                
                # event_info['open_status'] = venue_h_funcs.open_status(None, venue_h_funcs.to_list(None, result[12]), result[1])
                
                # # If a region is given, compare the current event-venue with the list of region_venues_list
                # if region_venues_list is not None:
                #     # Iterate through the venues list
                #     for venue in region_venues_list:
                #         if venue[1] == event_info['venue_id']:
                #             events.append(event_info)
                        
                # else:
                #     events.append(event_info)
                
            events.sort(key=lambda eventsgrouped: eventsgrouped['time'])

            events_grouped_iter = groupby(events, lambda eventsgrouped: eventsgrouped['date'])

            for w, g in events_grouped_iter:
                try:
                    events_grouped[str(w)]
                except KeyError:
                    events_grouped[str(w)] = []

                for e in g:
                    events_grouped[str(w)].append(e)
        
        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
        return response_builder.build_res(None, events_grouped, "events", request, stime, {})
    
    @connector_for_class_method
    def pending(self, cursor, request):

        stime = time.time()
        
        base_sql = "SELECT artists.name, venues.name, gigs.uuid, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.uuid, venues.uuid, venues.usually_ticketed, venues.hours_weekday, gigs.description, gigs.event_link, gigs.source_id, gigs.user_id, gigs.active, gigs.date_added \
            FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) \
            INNER JOIN venues ON gigs.venue_id = venues.venue_id)"
        
        start_day_dt = (dt.today())

        date_start = start_day_dt.strftime("%Y") + "-" + start_day_dt.strftime("%m") + \
            "-" + start_day_dt.strftime("%d")

        sql_mod = "WHERE `date` >= '{}'".format(date_start)
        sql_only_active = "AND artists.active = True AND venues.active = True AND gigs.pending = True"
        
        sql = base_sql + sql_mod + sql_only_active
        cursor.execute(sql)
        
        row_headers = [x[0] for x in cursor.description]
        row_headers[0] = "artist_name"
        row_headers[1] = "venue_name"
        row_headers[2] = "event_id"
        row_headers[9] = "artist_id"
        row_headers[10] = "venue_id"

        myresult = cursor.fetchall()
        events = []
        events_grouped = {}
        if (len(myresult) > 0):
            for result in myresult:

                event_info = dict(zip(row_headers, result))

                event_info['notes'] = ""
                event_info['level'] = 0
                
                # if stub
                if (artist_h_funcs.is_stub(None, cursor, result[9])):
                    event_info['level'] += 1
                    event_info['notes'] += "Is Stub"
                    
                
                # no description
                if (not result[13]):
                    event_info['level'] += 1
                    event_info['notes'] += " : Desc"
                
                # no event links
                if (not result[14] and not result[7]):
                    event_info['level'] += 1
                    event_info['notes'] += " : Links"
                
                # Get data source
                event_info['source'] = {}
                event_info['source']['name'] = db.get_source_name(None, cursor, result[15])
                event_info['source']['user'] = db.get_name_of_user(None, cursor, result[16])
                    
                events.append(event_info)                
                
            events.sort(key=lambda eventsgrouped: eventsgrouped['time'])

            events_grouped_iter = groupby(events, lambda eventsgrouped: eventsgrouped['date'])

            for w, g in events_grouped_iter:
                try:
                    events_grouped[str(w)]
                except KeyError:
                    events_grouped[str(w)] = []

                for e in g:
                    events_grouped[str(w)].append(e)
        
        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
        return response_builder.build_res(None, events_grouped, "events", request, stime, {})