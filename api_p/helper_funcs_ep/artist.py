import requests
from bs4 import BeautifulSoup
import json
import re
from ..helper_funcs import notices as n
import traceback
from ..sql.sql_connector import connector_for_class_post_method as connector_for_class_post_method

class artist_helper:
    def get_artist_info(self, request):
        try:
            
            # TODO do checks for proper triplej url
            try:
                tripj_link = request.query['url']
            except Exception:
                res = 'Incorrect request parameter'
                raise Exception

            if (tripj_link[0:3] != 'http'):
                tripj_link = 'http://' + tripj_link
                
            print(tripj_link)
            r = requests.get(tripj_link)
            html = r.text
            
            soup_raw_page = BeautifulSoup(html, "lxml")

            artist_info_raw = soup_raw_page.find_all(class_="module_artistinfo")
            soup_artist_info = BeautifulSoup(str(artist_info_raw[0]), "lxml")

            facebook_link = soup_artist_info.find_all('a', href=re.compile("facebook"))
            bandcamp_link = soup_artist_info.find_all('a', href=re.compile("bandcamp"))

            regex = r"<h3>(.*)<\/h3>\n<p>(.*)<\/p>"
            enc_info = re.findall(regex, str(soup_artist_info))
            info_json = { k[0]: k[1] for k in enc_info }
            info_json = json.dumps(info_json)
            info_json = json.loads(info_json)

            # Start to build new band info dict
            artist_name = soup_raw_page.find_all('h1', attrs={"id": "unearthed-profile-title"})
            for line in artist_name[0].strings:
                artist_name = line
                break
            # artist_name = artist_name[0].strings
            info_json['name'] = artist_name
            
            info_json['source'] = "2"

            # if social links available
            info_json['socials'] = {}
            info_json['socials']['unearthed_href'] = tripj_link
            if facebook_link:
                info_json['socials']["facebook_link"] = facebook_link[0]['href']
            else:
                info_json['socials']["facebook_link"] = None

            if bandcamp_link:
                info_json['socials']["website"] = bandcamp_link[0]['href']
            else: 
                info_json['socials']["website"] = None

            try:
                info_json['members'] = info_json['band members']
            except:
                info_json['members'] = None

            # remove from dict, seperate and re insert as nested dict
            if info_json['Genre'] != None:
                genre_list = info_json['Genre'].split(", ")
                info_json.pop('Genre', None)
                # print(genre_list)
                # genre_dict = { i : genre_list[i].lstrip() for i in range(0, len(genre_list) )  }
                info_json['genres'] = genre_list
            else:
                info_json['genres'] = None
            
            # remove un-used
            info_json.pop('Tags', None)
            info_json.pop('Sounds like', None)
            info_json.pop('Influences', None)
            info_json.pop('Unearthed artists we like', None)
            info_json.pop('Website', None)

            # Get Bio and add to info json
            bio = ''
            if soup_raw_page.find_all(class_="views-field-field-artist-bio"):
                for line in soup_raw_page.find_all(class_="views-field-field-artist-bio")[0].strings:
                    if line == '\n':
                        continue
                    else:
                        line = line.replace("\n", "").replace("\t", "")
                        bio += line + "\n"
                info_json['bio'] = bio
            else:
                info_json['bio'] = None

            # Get Location split region and state and add to info_json
            if soup_raw_page.find_all(lambda tag: tag.name == 'span' and tag.get('class') == ['location']):
                location = soup_raw_page.find_all(lambda tag: tag.name == 'span' and tag.get('class') == ['location'])[0].get_text()
                location_list = location.split(",")
                location_dict = { "region" : location_list[0].lstrip(),
                                "state_abr" : location_list[1].lstrip()
                                }
                info_json['location'] = location_dict
            else:
                info_json['location'] = { "region": None, "state_abr" : None}

            # print(info_json)
            res = info_json
        # try:
        #     res = myresult[0]
        #     artist_id = res[0]
        #     artist_info = {
        #     "artist_name": res[1],
        #     "members": res[2],
        #     "bio": res[3],
        #     "similar": res[5],
        #     "region": db.get_region(None, cursor, res[10]),
        #     "genre": db.get_genre(None, cursor, artist_id),
        #     "socials": {
        #         "website": res[4],
        #         "fb_link": res[6],
        #         "triple_j": res[11],
        #         },
        #     }


        except Exception as e:
            traceback.print_exc()
            res = n.print_note(None, 2, "triplej_artist_info", "Unknown error getting data: " + str(e))

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


