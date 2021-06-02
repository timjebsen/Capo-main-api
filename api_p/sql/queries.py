class queries:
    all_gigs = "SELECT artists.name, venues.name, gigs.uuid, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.artist_id, gigs.venue_id, \
    artists.uuid, venues.uuid, venues.usually_ticketed FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) \
    INNER JOIN venues ON gigs.venue_id = venues.venue_id)"

    artist_all = "SELECT artists.name, venues.name, gigs.uuid, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.uuid, venues.uuid, artists.artist_id, venues.usually_ticketed FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) INNER JOIN venues ON gigs.venue_id = venues.venue_id) WHERE gigs.artist_id = "

    venue_all = "SELECT artists.name, venues.name, gigs.uuid, `ticket`, `date`, `time`, `price`, `facebook_event_link`, venues.suburb, artists.uuid, venues.uuid, artists.artist_id, venues.usually_ticketed FROM ((`gigs` INNER JOIN artists ON gigs.artist_id = artists.artist_id) INNER JOIN venues ON gigs.venue_id = venues.venue_id) WHERE gigs.venue_id = "
    