import requests
import json
import re
from ..helper_funcs import notices as n
import traceback
from ..sql.sql_connector import connector_for_class_post_method as connector_for_class_post_method

class artist_model:
    def __init__(self , name, location, genres, bio, image, socials, triplej_link):
        self.name = name
        self.location = location
        self.genres = genres
        self.bio = bio
        self.image = image
        self.socials = socials
        self.triplej_link = triplej_link

class artist_helper:
    def get_artist_info(self, request):
        try:
            
            # TODO do checks for proper triplej url
            try:
                tripj_link = request.query['url']
            except Exception:
                res = 'Incorrect request parameter'
                raise Exception
            
            # * TipleJ have updated their website
            # * the old method is now deprecated.
            # * Now we have to build a new url
            # * and make the call to the TripleJ endpoint
            # New URI
            # https://www.abc.net.au/triplejunearthed/api/loader/UnearthedProfilesLoader?slug=<artist-name>&profileType=artist
            #

            artist_slug = re.search(r"/artist/(.*)", tripj_link)

            if not artist_slug.start():
                raise Exception('Could not resolve slug')

            artist_slug = artist_slug.group(1)
            
            url = "https://www.abc.net.au/triplejunearthed/api/loader/UnearthedProfilesLoader?slug="+artist_slug+"&profileType=artist"
            
            print(url)
            r = requests.get(url)

            if r.status_code != 200:
                raise Exception('Bad response from request. Got: '+str(r.status_code))

            try:
                artist_info_triplej = r.json()
            except requests.exceptions.JSONDecodeError:
                raise Exception('Bad response. Content not JSON. Got: '+str(r.text))

            if len(artist_info_triplej['profiles']) > 1:
                raise Exception('More than one artist profile found. Got: '+str(artist_info_triplej))
            elif len(artist_info_triplej['profiles']) < 1:
                raise Exception('No artist profile found.')

            artist_info_triplej = artist_info_triplej['profiles'][0]

            artist_info_obj = {}

            facebook_link = artist_info_triplej['socialLinksFacebook']
            spotify_link = artist_info_triplej['socialLinksSpotify']
            website_link = artist_info_triplej['socialLinksWebsite']
            instagram_link = artist_info_triplej['socialLinksInstagram']

            artist_info_obj['socials'] = {
                'spotify_link': spotify_link,
                'website': website_link,
                'facebook_link': facebook_link,
                'unearthed_href': "https://www.abc.net.au/triplejunearthed/artist/"+artist_slug,
            }

            artist_info_obj['name'] = artist_info_triplej['profileName']
            artist_info_obj['source'] = "2"
            artist_info_obj['members'] = artist_info_triplej['members']
            artist_info_obj['genres'] = artist_info_triplej['genres']
            artist_info_obj['bio'] =''
            artist_info_obj['bio'] = artist_info_triplej['bio']
            
            location_dict = { "region" : artist_info_triplej['region'],
                                "state_abr" : artist_info_triplej['stateId']
                                }

            artist_info_obj['location'] = location_dict

            res = artist_info_obj

        except Exception as e:
            traceback.print_exc()
            res = n.print_note(None, 2, "triplej_artist_info", "Error getting data: " + str(e))

        return res

    # Check for an artist existence from a given 'name'
    # This is not a perfect mechanism, however, the source
    # data is usually minimal (only containing a name).
    # The 'name' is prone to user input error, and exotic 
    # characters not input/parsed properly at the data source.
    # This will ultimately result in duplicate entries that 
    # will need to be managed manually.
    # TODO admin tool function to merge duplicated artists
    @connector_for_class_post_method
    def artist_exists(self, cursor, request):
        try:
            res = {}
            artist_name = request.query['name']
            sql = "SELECT `name`, `uuid` FROM `artists` WHERE `name` = %s"
            vals = (artist_name)
            cursor.execute(sql, vals)
            query_res = cursor.fetchall()
            try:
                if len(query_res) > 0:

                    # Artist found with name
                    # Only 1 row should be returned.
                    # Handle multiple just in case
                    if len(query_res) > 1:
                        res['status'] = 'OK'
                        res['message'] = 1
                        res['detailed'] = "Multiple artists found"
                        res['content'] = []
                        for each in query_res:
                            res['content'].append({
                                'name': each[0],
                                'id': each[1]
                            })
                        return res

                    else:
                        query_res = query_res[0]
                        res['status'] = 'OK'
                        res['message'] = 1
                        res['detailed'] = "One artist found"
                        res['content'] = {
                            'name': query_res[0],
                            'id': query_res[1]
                        }
                        return res
                else:
                    res['status'] = 'OK'
                    res['message'] = 0
                    res['detailed'] = 'No artist found with name: ' + artist_name
                    return res
            except Exception:
                res['status'] = 'FAIL'
                res['message'] = 'error'
                res['detailed'] = n.print_note(None, 2, "artist_helper.check_exist", "Unknown error. See log for details ")
                traceback.print_exc()
                return res

        except:
            res['status'] = 'FAIL'
            res['message'] = 'error'
            res['detailed'] = n.print_note(None, 2, "artist_helper.check_exist", "Unknown error. See log for details ")
            traceback.print_exc()
            return res


