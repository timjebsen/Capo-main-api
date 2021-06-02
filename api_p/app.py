# from aiohttp import web
# import json
# import mysql.connector
# import time
# from itertools import groupby
# import datetime
# from datetime import datetime as dt
# from datetime import timedelta

# import get
# # import post
# import config
# import sql_connector

# num = 0
# num_of_gigs = 0

# base_sql = "SELECT artists.name, venues.name, `gig_id`, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.artist_id \
#     FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) \
#     INNER JOIN venues ON gigs.venue_id = venues.venue_id)"

# # meta_data = {
# #     "rqst": "", # Name of request. "todaysGigs", "rowGigs"...
# #     "time_rcvd": None, # Time of reception of rqst
# #     "time_sent": None, # Time response sent
# #     "num_of_gigs": int, # Num of gigs in list
# #     "ngt": bool, # NGT = No gigs today. Is used to update "Today in loc: X Gigs", and display message at start of gig list.
# #                  # If false, and list > 0, then gigs are returned from row_gigs

# # }

# def print_req_info():
#     print("---------------------")
#     print("Request: {}".format(request.path))
#     print("Global Req. number: ", num)
#     print("Client: " + request.host)
#     print("Origin IP: " + request.remote)


# def next_weekday(d, weekday):
#     days_ahead = weekday - d.weekday()
#     if days_ahead <= 0:  # Target day already happened this week
#         days_ahead += 7
#     return d + timedelta(days_ahead)


# def get_all_gigs():
#     global num_of_gigs


#     mycursor.execute(sql)
#     row_headers = [x[0] for x in mycursor.description]
#     row_headers[0] = "artist_name"
#     row_headers[1] = "venue_name"
#     myresult = mycursor.fetchall()
#     mydb.commit()
#     gigs = []
#     if (len(myresult) > 0):
#         num_of_gigs = len(myresult)
#         for result in myresult:
#             gigs.append(dict(zip(row_headers, result)))

#         gigs.sort(key=lambda gigsg: gigsg['date'])
#         gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['date'])
#         gigs_grouped = {}

#         for t, g in gigs_grouped_iter:
#             gigs_grouped[str(t)] = []
#             for e in g:
#                 gigs_grouped[str(t)].append(e)

#     else:
#         gigs_grouped = {}

#     return gigs_grouped


# def get_row_gigs():
#     global num_of_gigs
#     mycursor = mydb.cursor()
#     date_today = dt.today().strftime("%Y") + "-" + dt.today().strftime("%m") + \
#         "-" + dt.today().strftime("%d")
#     date_eow = next_weekday(dt.today(), 6).strftime("%Y") + "-" + next_weekday(
#         dt.today(), 6).strftime("%m") + "-" + next_weekday(dt.today(), 6).strftime("%d")

#     sql_mod = "WHERE `date` BETWEEN '{}' AND '{}'".format(date_today, date_eow)
#     sql = base_sql + sql_mod

#     mycursor.execute(sql)
#     row_headers = [x[0] for x in mycursor.description]
#     row_headers[0] = "artist_name"
#     row_headers[1] = "venue_name"
#     myresult = mycursor.fetchall()
#     mydb.commit()
#     gigs = []
#     if (len(myresult) > 0):
#         num_of_gigs = len(myresult)
#         for result in myresult:
#             gigs.append(dict(zip(row_headers, result)))

#         gigs.sort(key=lambda gigsg: gigsg['date'])
#         gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['date'])
#         gigs_grouped = {}

#         for t, g in gigs_grouped_iter:
#             gigs_grouped[str(t)] = []
#             for e in g:
#                 gigs_grouped[str(t)].append(e)

#     else:
#         gigs_grouped = {}
#         # gigs_grouped[0] = "ngrow. todays date: {}. date eow: {}".format(
#         #     date_today, date_eow)
#         # gigs_grouped[1] = sql

#     return gigs_grouped


# async def todays_gigs(request):
#     global num
#     global num_of_gigs
    
#     num += 1
#     print("---------------------")
#     print("Request: {}".format(request.path))
#     print("Global Req. number: ", num)
#     print("Client: " + request.host)
#     print("Origin IP: " + request.remote)
#     stime = time.time()

#     date_today = dt.today().strftime("%Y") + "-" + dt.today().strftime("%m") + \
#         "-" + dt.today().strftime("%d")
#     # date_today = '2020-09-04'
#     sql_mod = "WHERE `date`='{}'".format(date_today)
#     sql = base_sql + sql_mod
#     mycursor.execute(sql)
#     row_headers = [x[0] for x in mycursor.description]
#     row_headers[0] = "artist_name"
#     row_headers[1] = "venue_name"
#     myresult = mycursor.fetchall()
#     mydb.commit()
#     gigs = []
#     gigs_grouped = {}
#     if (len(myresult) > 0):
#         num_of_gigs = len(myresult)
#         gigs_today = True
#         group_mode = 0
#         for result in myresult:
#             gigs.append(dict(zip(row_headers, result)))

#         gigs.sort(key=lambda gigsg: gigsg['time'])
#         gigs_grouped_iter = groupby(gigs, lambda gigsg: gigsg['time'])

#         for t, g in gigs_grouped_iter:
#             gigs_grouped[t] = []
#             for e in g:
#                 gigs_grouped[t].append(e)
#     else:
#         gigs_today = False
#         group_mode = 1
#         # gigs_grouped = get_row_gigs()
#         gigs_grouped = get_all_gigs()

#     meta_data = {
#         "rqst": request.path,
#         "time_rcvd": stime,
#         "time_sent": time.time(),
#         "num_of_gigs": num_of_gigs,
#         "gigs_today": gigs_today,
#         "group_mode": group_mode
#     }
#     gig_list_final = {}
#     gig_list_final["meta"] = meta_data
#     gig_list_final["gig_list"] = gigs_grouped

#     etime = time.time()

#     print("Time: " + str((etime - stime)*1000) + " ms")
#     # time.sleep(5)

#     return web.Response(text=json.dumps(gig_list_final, indent=4, sort_keys=True, default=str), status=200)


# async def search_index(request):
#     global num
#     num += 1
#     mycursor = mydb.cursor()
#     print("---------------------")
#     print("Request: {}".format(request.path))
#     print("Global Req. number: ", num)
#     print("Client: " + request.host)
#     print("Origin IP: " + request.remote)
#     stime = time.time()

#     # ! DO NOT CHANGE ORDER OF THESE SQL QUERIES
#     # ! THE ORDER DICTATES THE 'dbtbl' ID
#     # ! THIS IS USED IN THE SEARCH RESPONSE LABELS
#     sql_list = ["SELECT `artist_id`, `name` FROM `artists`",
#                 "SELECT `venue_id`, `name` FROM `venues`",
#                 "SELECT * FROM `genres`",
#                 "SELECT `reg_id`, `region` FROM `regions`"]

#     search_index_list = []
#     i = 0
#     for query in sql_list:
#         mycursor.execute(query)
#         # row_headers = [x[0] for x in mycursor.description]
#         # row_headers[0] = "artist_name"
#         # row_headers[1] = "venue_name"
#         myresult = mycursor.fetchall()
#         mydb.commit()
#         for each_row in myresult:
#             item = {
#                 "dbid": each_row[0],
#                 "dbtbl": i,
#                 "text": each_row[1]
#             }
#             search_index_list.append(item)

#         i += 1

#     etime = time.time()

#     print("Time: " + str((etime - stime)*1000) + " ms")

#     return web.Response(text=json.dumps(search_index_list, indent=4, sort_keys=True, default=str), status=200)


# async def row_gigs(request):
#     global num
#     num += 1
#     print("---------------------")
#     print("Request: {}".format(request.path))
#     print("Global Req. number: ", num)
#     print("Client: " + request.host)
#     print("Origin IP: " + request.remote)

#     stime = time.time()
#     gigs_grouped = {}
#     gigs_grouped = get_row_gigs()

#     meta_data = {
#         "rqst": request.path,
#         "time_rcvd": stime,
#         "time_sent": time.time(),
#         "num_of_gigs": num_of_gigs,
#         "gigs_today": False,
#         "group_mode": 1
#     }
#     gig_list_final = {}.today_all

#     print("Time: " + str((etime - stime)*1000) + " ms")
#     # time.sleep(5)

#     return web.Response(text=json.dumps(gig_list_final, indent=4, sort_keys=True, default=str), status=200)

# async def get_artist_info(request):
#     global num
#     num += 1
#     print_req_info()

#     stime = time.time()
    
#     artist_id = request.query['id']
#     sql = "SELECT * FROM `artists` WHERE `artist_id` ={}".format(artist_id)

#     mycursor = mydb.cursor()
#     mycursor.execute(sql)
#     myresult = mycursor.fetchall()
#     mydb.commit()
#     res = myresult[0]
#     artist_info = {
#         "artist_name": res[1],
#         "members": res[2],
#         "bio": res[3],
#         "website": res[4],
#         "similar": res[5],
#         "facebook_link": res[6],
#     }

#     etime = time.time()

#     print("Time: " + str((etime - stime)*1000) + " ms")
#     # time.sleep(5)

#     return web.Response(text=json.dumps(artist_info, indent=4, sort_keys=True, default=str), status=200)

# # async def add_ind_gig(request):
    

# app = web.Application()
# app.add_routes([web.get('/today', todays_gigs),
#                 web.get('/rowGigs', row_gigs),
#                 web.get('/searchIndex', search_index),
#                 web.get('/artistInfo', get_artist_info),
#                 # web.post('/addIndGig', add_ind_gig)
#                 ])
# web.run_app(app, port=12122)
