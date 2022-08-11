from datetime import datetime as dt
import time
from itertools import groupby
from ..sql.queries import queries as queries
from ..helper_funcs import h_funcs as h_funcs
from ..sql.sql_connector import connector_for_class_method
class row:
    @connector_for_class_method
    def get_row(self, cursor, request):
        stime = time.time()
        gigs_grouped = {}

        # Build dates for query
        date_today = dt.today().strftime("%Y") + "-" + dt.today().strftime("%m") + \
            "-" + dt.today().strftime("%d")
        date_eow = h_funcs.next_weekday(None, dt.today(), 6).strftime("%Y") + "-" + h_funcs.next_weekday(None,
            dt.today(), 6).strftime("%m") + "-" + h_funcs.next_weekday(None, dt.today(), 6).strftime("%d")

        sql_mod = "WHERE `date` BETWEEN '{}' AND '{}'".format(date_today, date_eow)
        sql = queries.all_gigs + sql_mod

        cursor.execute(sql)
        row_headers = [x[0] for x in cursor.description]
        row_headers[0] = "artist_name"
        row_headers[1] = "venue_name"
        myresult = cursor.fetchall()

        gigs = []
        if (len(myresult) > 0):
            # num_of_gigs = len(myresult)
            for result in myresult:
                gigs.append(dict(zip(row_headers, result)))

            gigs.sort(key=lambda gigsg: gigsg['date'])
            gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['date'])
            gigs_grouped = {}

            for t, g in gigs_grouped_iter:
                gigs_grouped[str(t)] = []
                for e in g:
                    gigs_grouped[str(t)].append(e)

        else:
            gigs_grouped = {}

        gig_list_final = {}
        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
        
        return gig_list_final