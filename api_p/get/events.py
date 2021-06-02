import time
from datetime import datetime as dt
import datetime
from ..sql.sql_connector import connector_for_class_method as connector_for_class_method
from ..sql.queries import queries as q
from ..helper_funcs import notices as n
from ..helper_funcs import db_funcs as db
from itertools import groupby
from ..helper_funcs import response_builder as response_builder

# TODO Rename module to upcoming. Had to move to a seperate module due to circular imports
class upcoming:
    ### Upcomiong returns a dict of gigs grouped by date for a given artist or venue
    #  TODO update to return only future events. Currently returns all events associated with query
    #  TODO deprecate art_or_ven. Perform a check on id to determine type
    def upcoming(self, art_or_ven, id, request, cursor):
        event_list = {}
        id = str(id)
        try:
            if( art_or_ven == 'artist'):
                sql = q.artist_all + id
            elif (art_or_ven == 'venue'):
                sql = q.venue_all + id
            else:
                raise ValueError
            # print(sql)
            cursor.execute(sql)
            myresult = cursor.fetchall()

            try:
                gigs = []
                row_headers = [x[0] for x in cursor.description]
                #  Re-name headers. Id's are overwritten with uuid's 
                row_headers[0] = "artist_name"
                row_headers[1] = "venue_name"
                row_headers[2] = "event_id"
                row_headers[9] = "artist_id"
                row_headers[10] = "venue_id"

                for each in myresult:
                    gig_info = dict(zip(row_headers, each))
                    gig_info['genre'] = db.get_genre(None, cursor, each[11])
                    gig_info['artist_id'] = each[9]
                    gigs.append(gig_info)

                gigs.sort(key=lambda gigsg: gigsg['time'])
                gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['date'])
                gigs_group = {}

                for w, g in gigs_grouped_iter:
                    gigs_group[str(w)] = []
                    for e in g:
                        gigs_group[str(w)].append(e)

                event_list = response_builder.build_res(None, gigs_group, "gig_list", request, 0, {})
                
            except IndexError:
                n.print_note(None, 0, "upcoming", "Upcoming has no events for: " + id + " - type: " + str(art_or_ven))
                event_list = {}
        except ValueError:
            n.print_note(None, 2, "upcoming", "art_or_ven Value must be 0 or 1. Given: " + str(art_or_ven))
        
        return event_list

    # Returns number of "future" gigs for a specified criteria
    # Used for location index
    def num_upcoming(self, cursor, criteria, id):
        gigs = 0
        id = str(id)
        try:
            if( criteria == 'artist'):
                sql = "SELECT COUNT(*) FROM gigs WHERE artist_id ="  + id
            elif (criteria == 'venue'):
                sql = "SELECT COUNT(*) FROM gigs WHERE venue_id ="  + id

            # TODO number of gigs for a region
            # elif (criteria == 'region'):
            #     sql = "SELECT COUNT(*) FROM gigs WHERE _id ="  + id
            else:
                raise ValueError
            # print(sql)
            cursor.execute(sql)
            myresult = cursor.fetchall()

            try:
                gigs = myresult[0][0]

            except IndexError:
                n.print_note(None, 0, "num_upcoming", "Upcoming has no events for: " + id + " - type: " + str(criteria))
        except ValueError:
            n.print_note(None, 2, "num_upcoming", " 'artist' or 'venue' only. Given: " + str(criteria))
        
        return gigs