from datetime import datetime as dt
import time
from itertools import groupby
from ..sql.sql_connector import connector
from .all import get_all_gigs as get_all_gigs
from ..helper_funcs import response_builder as response_builder

base_sql = "SELECT artists.name, venues.name, `gig_id`, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.artist_id \
    FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) \
    INNER JOIN venues ON gigs.venue_id = venues.venue_id)"


@connector
def get_today_all(cursor, request):
    # print("connection before"+str(cursor.open))
    # with cursor:
        # cursor = d
        # print('here')
    gigs = []
    gigs_grouped = {}
    num_of_gigs = 0
    gigs_today = None
    group_mode = None

    stime = time.time()
    date_today = dt.today().strftime("%Y") + "-" + dt.today().strftime("%m") + \
        "-" + dt.today().strftime("%d")
    # date_today = '2020-09-04'
    sql_mod = "WHERE `date`='{}'".format(date_today)
    sql_only_active = "AND artists.active = True AND venues.active = True"
    sql = base_sql + sql_mod + sql_only_active

    cursor.execute(sql)
    
    row_headers = [x[0] for x in cursor.description]
    row_headers[0] = "artist_name"
    row_headers[1] = "venue_name"
    myresult = cursor.fetchall()
    # cursor.commit()

    if (len(myresult) > 0):
        num_of_gigs = len(myresult)
        gigs_today = True
        group_mode = 0
        for result in myresult:
            gigs.append(dict(zip(row_headers, result)))

        gigs.sort(key=lambda gigsg: gigsg['time'])
        gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['time'])

        for t, g in gigs_grouped_iter:
            gigs_grouped[t] = []
            for e in g:
                gigs_grouped[t].append(e)
    else:
        gigs_today = False
        group_mode = 1
        # print('here')
        gigs_grouped = get_all_gigs.get_all_gigs(None, cursor)
        for each in gigs_grouped:
            num_of_gigs += len(gigs_grouped[each])
        
    # Custom fields to add to metadata object
    meta_custom = {
        "gigs_today": gigs_today,
        "group_mode": group_mode,
    }

    etime = time.time()
    print("Time: " + str((etime - stime)*1000) + " ms")
        # time.sleep(5)

    
    # print("connection after "+str(db_conn.open))
    return response_builder.build_res(None, gigs_grouped, "gig_list", request, stime, meta_custom)
