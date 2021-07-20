#! /bin/python3
import json
from threading import Thread
from aiohttp import web
import aiohttp_cors
import traceback
from api_p import helper_funcs as h_funcs

from api_p.get import *
from api_p.post import *
from api_p.helper_funcs_ep import *


# -----------------------------------------------------------------

# TODO Get requests:
# index of all gigs currently available... to be used in calendar
# TODO: Replace internal debugger funcs with decorator funcs
# TODO Handle 404 redirect
# TODO standardise response onjects
# -----------------------------------------------------------------

# * GET resources ---------------------------------------------------------------------------

# * Deprecated in v0.2. Replaced with "events_today"
# Returns a list of event objects, grouped by time.
# If events are not available today, a list of upcoming
# events grouped by date is returned. This changing of data structure
# proves difficult to work with for front end apps.
# This is still in use for mobile app.
# TODO update mobile with new events endpoints.
async def todays_gigs(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await today(request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


# * v0.2 only
# Returns a list of events grouped by time for the current day.
# Will return an empty list with metadata
async def _events(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await events.day(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def events_month(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await events.month(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)
    
async def _events_all(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await events.all(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def _events_pending(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await events.pending(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def _event_info(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await gig.info(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def search_index(request):
    h_funcs.h_funcs.print_req_info(None, request)
    print("before func")
    res = await indexes.all(None)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def locations_index(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await indexes.locations(None)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def artists_index(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await indexes.artists(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def artist_regions_index(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await indexes.artist_regions(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def artist_genres_index(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await indexes.artist_genres(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def venues_index(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await indexes.venues(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


# async def row_gigs(request):
#     h_funcs.h_funcs.print_req_info(None, request)
#     res = await row.get_row(None, request)
#     return web.Response(text=json.dumps(res,
#                                         indent=4,
#                                         sort_keys=True,
#                                         default=str),
#                         status=200)


async def artist_info(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await get_artist.artist_from_req(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def venue_info(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await get_venue.venue_from_req(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def list_of_venues(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await venues_list.venues_all(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def gig_info(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await gig.get_gig_info(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def search_reg(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await search.by_region(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


# * Helper Func ===============================================
async def artist_info_from_triplej(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = artist_helper.get_artist_info(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def _venue_exist(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await venue_helper.venue_exist(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)
 
async def _update_missing_venue_images(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await venue_helper.add_venue_images(None,)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def _deactivate_closed_venues(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = await venue_helper.deactivate_closed_venues(None,)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def _artist_exists(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = artist_helper.artist_exists(None, request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

# * POST resources ---------------------------------------------------------------------------
# TODO Re-factor response status's

async def new_venue(request):
    h_funcs.h_funcs.print_req_info(None, request)
    data_json = await request.json()
    # print(data)
    res = post_venue.post_venue(None, data_json)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def new_venue_from_place_id(request):
    h_funcs.h_funcs.print_req_info(None, request)
    data_json = await request.json()
    res = post_venue.post_venue_from_place_id(None, data_json)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)

async def new_event(request):
    h_funcs.h_funcs.print_req_info(None, request)
    event_data = await request.json()
    res = post_event.post_event(None, request, event_data)
    if (res['status'] == 'FAIL'):
        staus_code = 500
    else:
        staus_code = 200
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def new_artist(request):
    h_funcs.h_funcs.print_req_info(None, request)
    data_json = await request.json()
    res = post_artist.post_artist(None, request, data_json)
    if (res['status'] == 'FAIL'):
        staus_code = 500
    else:
        staus_code = 200
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=staus_code)

async def new_temp_artist(request):
    h_funcs.h_funcs.print_req_info(None, request)
    data_json = await request.json()
    res = post_artist.post_temp_artist(None, data_json)
    if (res['status'] == 'fail'):
        staus_code = 500
    else:
        staus_code = 200
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=staus_code)

async def update_venue(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = {}
    try:
        data_json = await request.json()
        res = post_venue.update(None, data_json)
    except:
        traceback.print_exc()
        
        res['status'] = 'fail'

    if (res['status'] == 'fail'):
        staus_code = 500
    else:
        staus_code = 200
    return web.Response(
                        text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        
                        status=staus_code,
                        )

async def deactivate_venue(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = {}
    try:
        data_json = await request.json()
        res = post_venue.deactivate(None, data_json)
    except:
        traceback.print_exc()
        
        res['status'] = 'FAIL'

    if (res['status'] == 'FAIL'):
        staus_code = 500
    else:
        staus_code = 200
    return web.Response(
                        text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        
                        status=staus_code,
                        )

async def disable_event(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = {}
    try:
        data_json = await request.json()

        res = post_event.disable(None, data_json)
    except:
        traceback.print_exc()
        
        res['status'] = 'FAIL'

    if (res['status'] == 'FAIL'):
        staus_code = 500
    elif (res['status'] == 'OK') :
        staus_code = 200
    
    return web.Response(
                        text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        
                        status=staus_code,
                        )

# * Helper funcs ----------------------------------
async def _get_places_id(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = get_places_id(request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)


async def _get_place_details(request):
    h_funcs.h_funcs.print_req_info(None, request)
    res = get_place_details(request)
    return web.Response(text=json.dumps(res,
                                        indent=4,
                                        sort_keys=True,
                                        default=str),
                        status=200)




app = web.Application()
app.add_routes([
    # * Read
    web.get('/v0.1/events/today', todays_gigs),
    web.get('/event', _event_info),
    web.get('/events', _events),
    web.get('/events/month', events_month),
    web.get('/events/all', _events_all),
    web.get('/events/pending', _events_pending),
    web.get('/index/search', search_index),
    web.get('/index/venue/locations', locations_index),
    web.get('/index/artists', artists_index),
    web.get('/index/venues', venues_index),
    web.get('/index/artist/regions', artist_regions_index),
    web.get('/index/artist/genres', artist_genres_index),
    web.get('/artist/info', artist_info),
    web.get('/venue/info', venue_info),
    web.get('/search/region', search_reg),
    web.get('/venues', list_of_venues),

    # * Update
    # See CORS resources
    # web.put('/event/disable', disable_event),

    # * Create
    web.post('/event/new', new_event),
    web.post('/venue/new', new_venue),
    web.post('/venue/new/pid', new_venue_from_place_id),
    web.post('/artist/new', new_artist),
    web.post('/artist/new_temp', new_temp_artist),

    # * Helper
    web.get('/venue/places_id_from_search', _get_places_id),
    web.get('/venue/details_from_pid', _get_place_details),
    web.get('/venue/exists', _venue_exist),
    web.get('/venue/update_missing_images', _update_missing_venue_images),
    web.get('/venue/deactivate_closed', _deactivate_closed_venues),
    web.get('/artist/helper/triplej', artist_info_from_triplej),
    web.get('/artist/exists', _artist_exists),

])


# * CORS is required for admin tool fnctionality
# Used for updating venue details with javascript, rather than HTML forms
# Aiohttp does not support CORS, a plugin module is used instead
# ! When migrating to production env. update origin restrictions.
cors = aiohttp_cors.setup(app)

resource1 = cors.add(app.router.add_resource("/venue/update"))
route1 = cors.add(
    resource1.add_route("POST", update_venue), {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            # # max_age=3600,
        )
    })

resource2 = cors.add(app.router.add_resource("/venue/deactivate"))
route2 = cors.add(
    resource2.add_route("POST", deactivate_venue), {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            # # max_age=3600,
        )
    })

resource3 = cors.add(app.router.add_resource("/event/disable"))
route3 = cors.add(
    resource3.add_route("POST", disable_event), {
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            # # max_age=3600,
        )
    })

web.run_app(app, port=12122)