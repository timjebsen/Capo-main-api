# Endpoint for adding an individual Gig to the db
# Duplicates/pre-exisitng data checks to be included...
import time
import json
from ..sql.sql_connector import connector_for_class_post_method
from ..helper_funcs import db_funcs as db_funcs, event_h_funcs
from ..helper_funcs import notices as n
import datetime
import traceback
from ..exceptions import *


# TODO Perform input data type check to determin singular gig or list of gigs
# * if data contains "gigs" key -> data is list of gigs
# * else data is singular gig

class event:
    @connector_for_class_post_method
    def post_event(self, cursor, request, gig_info):
        # Expects:
        # new_event = {
        #     "artist_name": str, --> OPTIONAL
        #     "artist_id": str, --> OPTIONAL
        #     "venue_name": str, --> OPTIONAL
        #     "venue_id": str, --> OPTIONAL
        #     "google_place_id", str --> OPTIONAL
        #     "ticket": bool(int),
        #     "price": int,
        #     "facebook_event_link": str, --> OPTIONAL
        #     "event_link": str, --> OPTIONAL
        #     "duration": int, --> OPTIONAL
        #     "date": str(YYYY-MM-DD),
        #     "time": int(time)
        # } 
        # 
        # For name or Id, at least one must be given.
        # 
        try:
            # ! Check for a temp status
            # ! Temp is used when an artist cannot be identified and the event title
            # ! has to be used in place of the artist name
            # TODO do not show temp artists in searches/indexes
            # TODO disable "view artist" in front end
            #  Get internal id from uuid or name

            if (gig_info['artist_id'] != None):
                artist_id = db_funcs.get_id_from_uuid(None, cursor, gig_info['artist_id'])
            elif (gig_info['artist_name'] != None):
                artist_id = db_funcs.get_id_from_name(None, cursor, 'artist', gig_info['artist_name'])
            else:
                raise DataError(n.print_note(None, 2, "post_event", "Could not determine artist id. Check uuid/name"))

            if (gig_info['venue_id'] != None):
                venue_id = db_funcs.get_id_from_uuid(None, cursor, gig_info['venue_id'])
            elif (gig_info['venue_name'] != None):
                venue_id = db_funcs.get_id_from_name(None, cursor, 'venue', gig_info['venue_name'])
            elif (gig_info['google_place_id'] != None):
                venue_id = db_funcs.get_id_using_triplej_or_gplacesid(None, cursor, 'venues', gig_info['google_place_id'])
            else:
                raise DataError(n.print_note(None, 2, "post_event", "Could not determine a method to get venue id. Check uuid/name/place_id"))
            
            # Prepare source
            # get the source name
            # Try and match it with existing source name to get sourcce id
            # if not exists, create new source record.
            
            # Any errors default to 'unknown' user and and source
            source_id = db_funcs.get_source_id(None, cursor, gig_info['source_name'], gig_info['source_link'])
            user_id = db_funcs.get_user_id(None, cursor, gig_info['user_name'])

            # Convert string to datetime object
            date = datetime.datetime.strptime(gig_info['date'], '%Y-%m-%d')

            # * Some key vals may not exist. This will raise key errors when trying to build obj
            # * If a key value does not exist, create a key val pair of None
            # TODO find a better way to check for key value pair existense/emptiness
            try:
                # If ticket is false, nullify the price if not null already
                if (gig_info['ticket'] == None and gig_info['price'] != None):
                    price = None
                elif (gig_info['ticket'] == False and gig_info['price'] != None ):
                    price = None
                else:
                    price = gig_info['price']
            except KeyError:
                gig_info['ticket'] = None
                price = None

            try:
                gig_info['facebook_event_link']
            except KeyError:
                try:
                    gig_info['fb_link'] # 'fb_link' is deprectaed, check for it just in case
                except KeyError:
                    gig_info['facebook_event_link'] = None
            
            try:
                gig_info['event_link']
            except KeyError:
                gig_info['event_link'] = None
        
            try:
                gig_info['duration']
            except KeyError:
                gig_info['duration'] = None

            try:
                gig_info['duration']
            except KeyError:
                gig_info['duration'] = None

            try:
                gig_info['description']
            except KeyError:
                gig_info['description'] = None


            new_event_info = {
                "artist_id": artist_id,
                "venue_id": venue_id,
                "user_id": user_id,
                "source_id": source_id,
                "ticket": gig_info['ticket'],
                "date": date,
                "time": gig_info['time'],
                "price": price,
                "facebook_event_link": gig_info['facebook_event_link'],
                "event_link": gig_info['event_link'],
                "duration":gig_info['duration'],
                "description": gig_info['description']
            }

            res = db_funcs.insert_event(None, cursor, new_event_info)

            return res
        
        except KeyError as e:
            print(e)
            traceback.print_exc()
            res = {
                "status": "FAIL",
                "message": "Failed to creat new event.",
                "detailed": n.print_note(None, 2, "post_event", "Missing key value: "+ str(e)),
                
            }
            return res

        except Exception as e:
            print(e)
            traceback.print_exc()
            res = {
                "status": "FAIL",
                "message": "Failed to creat new event",
                "detailed": n.print_note(None, 2, "post_event", "Unexpected error in post_event. See logs for details"),
            }
            return res
        
    @connector_for_class_post_method
    def disable(self, cursor, data):
        try:
            res = {}
            # Data is a uuid of the event
            event_id = data['event_id']
            
            # event_h_funcs.disable(None, cursor, event_id)
            if (event_h_funcs.disable(None, cursor, event_id)):
                res['status'] = 'OK'
                res['message'] = 'Successfully disabled event'

            else:
                res['status'] = 'OK'
                res['message'] = 'Failed to disable event. Event already Disabled?'
            
            return res
        
        except Exception as e:
            print(e)
            traceback.print_exc()
            res = {
                "status": "FAIL",
                "message": "Failed to disable event",
                "detailed": n.print_note(None, 2, "disable", "Unexpected error in event disable. See logs for details"),
            }
            return res
            
