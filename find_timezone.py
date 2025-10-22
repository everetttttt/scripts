#!/usr/bin/env python3

# this script is being used to figure out the time it will be on my vacation.
# to work around daylight savings time and timezone differences
# ./find_timezone.py <location1> <home city> <location1 datetime>
# will spit out the location1 timezone at that datetime
# the home timezone at that datetime
# and the corresponding home time to put in your calendar

import os
import sys
import pytz

from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

def print_help() -> None:
    rel = os.path.relpath(__file__, os.getcwd())
    print(f'{rel} - convert a local time at location1 to the corresponding time at location2')
    print(f'Usage:')
    print(f'    {rel} "<location1>" "<location2>" YYYY-MM-DD HH:MM')
    print()

    sys.exit(0)


def check_location(location: str):
    geolocator = Nominatim(user_agent="timezone_converter")
    loc = geolocator.geocode(location)
    if not loc:
        print(f'Error: could not find location {location}')
        sys.exit(1)

    tz = get_timezone(loc.latitude, loc.longitude)
    if not tz:
        print(f'Error: could not determine timezone for {location}')
        sys.exit(1)

    return loc, tz
        

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    return tf.timezone_at(lat=lat, lng=lon)


def convert_and_print(location1, tz1, location2, tz2, date_str, time_str):
    # parse base datetime
    try:
        dt = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
    except ValueError:
        print(f'Error: date must be YYYY-MM-DD and time must be HH:MM. Provided date {date_str} and time {time_str}')
        sys.exit(1)

    local_tz1 = pytz.timezone(tz1)
    dt1 = local_tz1.localize(dt)
    local_tz2 = pytz.timezone(tz2)
    dt2 = dt1.astimezone(local_tz2)

    print(f'{"Location":30} | {"Timezone":20} | Datetime')
    print(f'{location1:30} | {tz1:20} | {dt1}')
    print(f'{location2:30} | {tz2:20} | {dt2}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print_help()

    if len(args) < 4:
        print(f'Error: not enough arguments')
        print_help()

    location1 = args[0]
    loc1_obj, tz1 = check_location(location1)

    location2 = args[1]
    loc2_obj, tz2 = check_location(location2)

    d = args[2]
    t = args[3]

    convert_and_print(location1, tz1, location2, tz2, d, t)
