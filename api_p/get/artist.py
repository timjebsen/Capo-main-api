from ..sql.sql_connector import connector_for_class_method
from ..sql.queries import queries as q
import time
from ..helper_funcs import notices as n
from ..helper_funcs import db_funcs as db
from .events import upcoming as get_event

class artist_info:
    @connector_for_class_method
    def artist_from_req(self, cursor, request):
        # TODO perform checks on incoming id and return appropriate response
        artist_id = request.query['id']

        # * 'request' is used as part of the response builder in full artist info
        # * upcoming_events function, but not in basic info...
        # TODO Refactor 'artist_info_basic' info for consistensy. Same for venue info...
        return artist_info.artist_info(None, cursor, request, artist_id)

    def artist_info(self, cursor, request, artist_id):
        res = {}
        stime = time.time()
        sql = "SELECT * FROM `artists` WHERE `uuid` = '{}' AND `active` = True".format(str(artist_id))
        
        cursor.execute(sql)
        myresult = cursor.fetchall()
        # cursor.commit()

        try:
            res = myresult[0]
            artist_id = res[0]
            artist_info = {
            "name": res[1],
            "id": res[12],
            "members": res[2],
            "bio": res[3],
            "similar": res[5],
            "region": db.get_region(None, cursor, res[10]),
            "genre": db.get_genre(None, cursor, artist_id),
            "socials": {
                "website": res[4],
                "fb_link": res[6],
                "triple_j": res[11],
                },
            }
            res = {
                "artist_info": artist_info,
                "upcoming_events": get_event.upcoming(None, 'artist', artist_id, request, cursor)
            }
        except IndexError:
            res = n.print_note(None, 2, "get_artist_info", "Error with with artist id: " + artist_id)
        
        etime = time.time()
        print("Time: " + str((etime - stime)*1000) + " ms")
        return res

    # Used for web app view event page that requires basic information about an artist
    def artist_info_basic(self, cursor, artist_id):
        res = {}
        stime = time.time()
        sql = "SELECT * FROM `artists` WHERE `uuid` = '{}' AND `active` = True".format(str(artist_id))
        
        cursor.execute(sql)
        myresult = cursor.fetchall()

        try:
            res = myresult[0]
            artist_id = res[0]
            
            artist_info = {
                "name": res[1],
                "id": res[12],
                "members": res[2],
                "bio": res[3],
                "similar": res[5],
                "region": db.get_region(None, cursor, res[10]),
                "genre": db.get_genre(None, cursor, artist_id),
                "socials": {
                    "website": res[4],
                    "fb_link": res[6],
                    "triple_j": res[11],
                    },
                "stub": res[16],
            }
            print(artist_info)
        except IndexError:
            res = n.print_note(None, 2, "get_artist_info", "Error with with artist id: " + artist_id)

        etime = time.time()

        print("Time: " + str((etime - stime)*1000) + " ms")
        
        return artist_info