import time
from datetime import datetime as dt
import datetime
from ..sql.sql_connector import connector_for_class_method as connector_for_class_method
from ..sql.queries import queries as q
from ..helper_funcs import notices as n
from ..helper_funcs import db_funcs as db
from itertools import groupby
from ..helper_funcs import response_builder as response_builder
from .venue import venue_info as venue_info
from .artist import artist_info as artist_info
from ..exceptions import *
import traceback

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
    base_sql = "SELECT artists.name, venues.name, gigs.uuid, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.uuid, venues.uuid, venues.usually_ticketed \
            FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) \
            INNER JOIN venues ON gigs.venue_id = venues.venue_id)"

    @connector_for_class_method
    def day(self, cursor, request):

        stime = time.time()
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
                event['genre'] = db.get_genre(None, cursor, result[9])
                gigs.append(event)

            gigs.sort(key=lambda gigsg: gigsg['time'])
            gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['time'])

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

    @connector_for_class_method
    def month(self, cursor, request):

        stime = time.time()
        
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
        gigs = []
        gigs_grouped = {}
        if (len(myresult) > 0):
            for result in myresult:
                # print(gig_info)
                gig_info = dict(zip(row_headers, result))
                # print(gig_info)
                gig_info['genre'] = db.get_genre(None, cursor, result[9])
                
                gigs.append(gig_info)
                
            gigs.sort(key=lambda gigsg: gigsg['time'])
            # print(gigs)

            gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['date'])
            # for each in gigs_grouped_iter:
            #     print()
            #     print(each)
            #     for r in each[1]:
            #         print(r)

            for w, g in gigs_grouped_iter:
                try:
                    gigs_grouped[str(w)]
                except KeyError:
                    gigs_grouped[str(w)] = []

                for e in g:
                    gigs_grouped[str(w)].append(e)
            
        
        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
            # time.sleep(5)
        
        # print("connection after "+str(db_conn.open))
        return response_builder.build_res(None, gigs_grouped, "events", request, stime, {})