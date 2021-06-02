# Endpoint for adding an individual Gig to the db
# Duplicates/pre-exisitng data checks to be included...
import sys
import time
import traceback
from datetime import datetime

from ..helper_funcs import db_funcs as db_funcs
from ..helper_funcs import notices as n
from ..sql.sql_connector import connector_for_class_post_method as connector_for_class_post_method
from ..exceptions import *

class post_artist:
    @connector_for_class_post_method
    def post_artist(self, cursor, request, data_json):
        try:
            res = "Begin post_artist"
            artist_data = data_json

            if type(artist_data) != dict:
                raise DataType()
            
            # if artists key exists, it indicates a list
            # TODO define list of objects with a more robust method
            # if "artists" in artist_data:
            #     artist_list = artist_data["artists_list"]
            #     res = post_artist_funcs.post_artist_list(None, cursor, artist_list)
            
            # # TODO define an info obj with a more robust method
            # elif len(artist_data) == 10 or len(artist_data) == 9:
            #     # TODO Perform if check to ensure singular venue data 

            else:
                res = post_artist_funcs.post_artist_ind(None, cursor, artist_data)
            
            # else:
            #     raise DataFormat()
        except DataType:
            res = n.print_note(None, 2, "post_artist", "Data not a dict. See logs for details")
        except DataFormat:
            res = n.print_note(None, 2, "post_artist", "Unknown dict format or objects. See logs for details")
        except:
            res = n.print_note(None, 2, "post_artist", "Unexpected error in post_artist. See logs for details")
            traceback.print_exc()

        return res
        
    @connector_for_class_post_method
    def post_temp_artist(self, cursor, event_title):
        # This handles an "artist" for an event where an explicit artist is unknown
        # All that is required is a "name", in most cases it will be a title of an 
        # event such as "Easter Sunday with the Brunswick Street Parade"
        # It was assumed at the creation of the db that each event will
        # have a title consisting of just the artist name. Therefore an event
        # requires an explicitly defined artist.
        # 
        # Scraping almost always returns an artist unknown to the db, therefore,
        # as an event requires an artist name the event cannot be added.
        # We do however have the title of the event, (which may, or may not contain
        # an artist name). So we must create a temporary artist that has only a name
        # which is the title of the event.
        # 
        # Ideally, this title would be put either straight into the event record
        # or in a seperate table, rather than creating an "artist". However, the
        # artist_id is an fk making it a required value. The quickest workaround
        # is therefore to create a new entire artist record. There are other more 
        # robust solutions however this is v0.1, so the quick and dirty method is used.
        # 
        # The new "artist" is assigned the "temp" value, hiding it from searches,
        # and disabling the "view artist" buttons on the front ends.
        # 
        # Expects:
        # 
        # event_title_info  = {
        #     "name": str,
        #     "source": int # For future use
        # }
        # 
        res = {}
        try:
            # source_name = event_title_info['source_name']
            # source_link = event_title_info['source_link']
            # # Create a new source if doesnt exist

            # TODO create new sources from a given source name file
            source_id = 8

            # Region id is a fk therefore a required field
            # For temp atists, no region is given. Id 35 is a "null" value
            region_id = 35

            sql = "INSERT INTO `artists` (name, source_id, last_edit, reg_id, uuid, temp) VALUES (%s, %s, %s, %s, UUID(), 1)"
            val = (event_title, source_id, datetime.now(), region_id)
            cursor.execute(sql, val)

            # get the uuid from last insert
            uuid = db_funcs.get_uuid_from_id(None, cursor, cursor.lastrowid, "artist")

            res['status'] = 'OK'
            res['note'] = n.print_note(None, 0, "post_temp_artist", "Successfully created a temp artist: " + event_title )
            res['artist_id'] = uuid
            return res

        except Exception as error:
            res['status'] = 'FAIL'
            res['note'] = n.print_note(None, 2, "post_artist_ind", "Unexpected error in post_temp_artist:")
            traceback.print_exc()
            return res

class post_artist_funcs:
    def post_artist_ind(self, cursor, artist_info):
        # 
        # Object model for new artist
        # 
        # artist_info  = {
        #     "genres": list,
        #     "location": {
        #         "region": str,
        #         "state_abr": str
        #     },
        #     "name": str,
        #     "bio": str,
        #     "members": str,
        #     "socials": {
        #         "facebook_link": str,
        #         "website": str,
        #         "unearthed_href": str,
        #         "spotify_link": str,
        #     },
        #     "source": int
        # }        
        # 
        res = {}
        try:
            # if (artist_info['source'] == 0):
            #     source_name = 'Triple J Unearthed'
                # source_link = "http://www.triplejunearthed.com/"

            # Empty objs to None
            for each_dp in artist_info:
                if each_dp is dict:
                    for each_dp2 in each_dp:
                        if each_dp2 == '' or each_dp2 == "":
                            artist_info[each_dp][each_dp2] = None
                elif artist_info[each_dp] == []:
                    artist_info[each_dp] = None
                elif artist_info[each_dp] == '' or artist_info[each_dp] == "":
                    artist_info[each_dp] = None
            
            source_name = artist_info['source']

            # Check source exists and get source ID
            source_id = db_funcs.get_source_id(None, cursor, source_name)

            # Check region
            # TODO Re-factor into function
            sql = "SELECT 1 FROM `regions` WHERE `region` = %s AND `state_abr` = %s"
            val = (artist_info["location"]["region"],artist_info["location"]["state_abr"])
            cursor.execute(sql, val)
            myresult = cursor.fetchall()
            if not myresult:
                sql = "INSERT INTO `regions` (region, state_abr) VALUES (%s, %s);"
                val = (artist_info["location"]["region"],artist_info["location"]["state_abr"])
                cursor.execute(sql, val)
                region_id = cursor.lastrowid
            else:
                sql = "SELECT * FROM `regions` WHERE `region` = %s AND `state_abr` = %s"
                val = (artist_info["location"]["region"],artist_info["location"]["state_abr"])
                cursor.execute(sql, val)
                myresult = cursor.fetchall()
                region_id = myresult[0][0]

            # Create and nullify missing key.
            # Due to addition of spotify link,
            # front ends may not have been updated yet
            try:
                if not artist_info['socials']["spotify_link"]:
                    artist_info['socials']["spotify_link"] = None
            except:
                artist_info['socials']["spotify_link"] = None
                
            print(artist_info)
            if (source_name == 'triple_j_unearthed'):
                check_exist_column = "unearthed_href"
                check_exist_value = artist_info['socials']["unearthed_href"]
            else:
                check_exist_column = 'name'
                check_exist_value = artist_info["name"]

            check_exist_table = "artists"

            # Check  artist for existence
            # Add artist -> get last artist id 
            # then checkeck if genre exists
            # add new genre if not exists
            # if exists get genre id
            # create new arist_genre line with genre id and artist id
            if (check_exist_value != ""):
                if not db_funcs.check_exist(None, cursor, check_exist_table, check_exist_column, check_exist_value): 
                    sql = "INSERT INTO `artists` (name, members, bio, website, facebook_link, source_id, last_edit, reg_id, unearthed_href, spotify_link, uuid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, UUID())"
                    val = (artist_info["name"], artist_info["members"], artist_info["bio"], artist_info['socials']["website"], artist_info['socials']["facebook_link"], source_id, datetime.now(), region_id, artist_info['socials']["unearthed_href"], artist_info['socials']["spotify_link"])
                    cursor.execute(sql, val)
                    artist_id = cursor.lastrowid
                    res = {
                        'status': 'OK',
                        'content':{
                            'note': 'Successfully created new artist',
                            'artist_id':db_funcs.get_uuid_from_id(None, cursor, artist_id, 'artist')
                        }
                    }
                    
                    res['content']['artist_id'] = db_funcs.get_uuid_from_id(None, cursor, artist_id, 'artist')
                    res['status'] = "OK"
                    n.print_note(None, 0, "post_artist_ind", "Successfully created new artist: " + artist_info["name"] )
                else:
                    raise Duplicate(n.print_note(None, 0, "post_artist_ind", "Artist already exists: " + artist_info["name"]))
                
                # Matches with formatted genre name. In future match should be done with raw format or uuid
                for genre in artist_info["genres"]:
                    sql = "SELECT `genre_id` FROM `genres` WHERE `genre` = %s"
                    val = (genre,)
                    cursor.execute(sql, val)
                    myresult = cursor.fetchall()
                    
                    # Add new genre if not exists
                    if not myresult:
                        sql = "INSERT INTO `genres` (genre) VALUES (%s)"
                        val = (genre,)
                        cursor.execute(sql, val)
                        genre_id = cursor.lastrowid
                        db_funcs.add_to_artist_genres(None, cursor, artist_id, genre_id)

                    else:
                        genre_id = myresult[0][0]
                        db_funcs.add_to_artist_genres(None, cursor, artist_id, genre_id)
            

        except KeyError as error:
            res = {
                'status': 'FAIL',
                'content':{
                    'note': n.print_note(None, 0, "post_artist_ind", "Incomplete data for artist: {}. Error at: {}".format(artist_info["name"], error))
                }
            }

        except Duplicate as e:
            # Duplicate error is not considered fatal. Return an 'OK' status with message
            res = {
                'status': 'OK',
                'content':{
                    'note': e,
                    'artist_id': db_funcs.get_uuid_from_id(None, cursor, db_funcs.get_id_using_triplej_or_gplacesid(None, cursor, "artists", artist_info['socials']["unearthed_href"]), "artist") 
                }
            }

        except Exception as error:
            res = {
                'status': 'FAIL',
                'content':{
                    'note': n.print_note(None, 2, "post_artist_ind", "Unexpected error in post_artist_ind:" + error.with_traceback)
                }
            }

        return res

    def post_artist_list(self, cursor, artist_list):
        artist_list = artist_list["artists"]

        for i in range(len(artist_list)):
            artist_info = artist_list[str(i)]
            res = post_artist_funcs.post_artist_ind(None, cursor, artist_info)

        return res

    

