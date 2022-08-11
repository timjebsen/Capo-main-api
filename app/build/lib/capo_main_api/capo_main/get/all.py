from datetime import datetime as dt 
from itertools import groupby

from ..sql import queries as q
from ..helper_funcs import db_funcs as db

# TODO get_all_gigs to be deprecated. Replaced with upcoming
class get_all_gigs:
    def get_all_gigs(self, cursor):
        cursor.execute(q.queries.all_gigs)
        row_headers = [x[0] for x in cursor.description]
        row_headers[0] = "artist_name"
        row_headers[1] = "venue_name"
        row_headers[2] = "gig_id"
        row_headers[11] = "artist_id"
        row_headers[12] = "venue_id"
        myresult = cursor.fetchall()
        gigs = []
        if (len(myresult) > 0):
            num_of_gigs = len(myresult)
            for result in myresult:
                gig_info = dict(zip(row_headers, result))
                gig_info['genre'] = db.get_genre(None, cursor, result[9])
                
                gigs.append(gig_info)

            gigs.sort(key=lambda gigsg: gigsg['date'])
            gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['date'])
            gigs_grouped = {}

            for w, g in gigs_grouped_iter:
                gigs_grouped[str(w)] = []
                for e in g:
                    gigs_grouped[str(w)].append(e)

        else:
            gigs_grouped = {}
        
        return gigs_grouped


