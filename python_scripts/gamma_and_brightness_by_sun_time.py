import sys
import os
import time
import argparse
from utils.sun import Sun
from utils.geo_location import from_ISO_6709
import datetime


parser = argparse.ArgumentParser()
parser.add_argument('-c','--coordinates', help='GPS coordintes in ISO 6709 format', required=True)
parser.add_argument('-g','--gamma-night', help='Gamma values on full night mode, format <float>:<float>:<float>, default 1:0.8:0.6', default="1:0.8:0.6")
parser.add_argument('-G','--gamma-day', help='Gamma values on full day mode, format <float>:<float>:<float>, default 1:1:1', default="1:1:1")
parser.add_argument('-b','--brightness-night',  help='Brightness value on full night mode, default 0.8', default="0.7")
parser.add_argument('-B','--brightness-day',  help='Brightness value on full day mode, default 1', default="1")
args = parser.parse_args()


sun = Sun()

total_transition_time=7200 #seconds
half_transition_time=total_transition_time/2 #seconds

def to_time_in_current_timezone(suntime):
    timezone_offset=time.timezone;
    utc_hours = suntime['hr']
    utc_mins = suntime['min']
    utc_time = (utc_hours * 60 + utc_mins) * 60
    local_time = utc_time - timezone_offset;
    local_hours = (int(local_time / 3600) + 24) % 24
    local_min = int((local_time % 3600) / 60)
    return (local_hours * 60 + local_min) * 60

def format_time(local_time):
    local_hours = (int(local_time / 3600) + 24) % 24
    local_min = int((local_time % 3600) / 60)
    return '{0:02d}:{1:02d}'.format(local_hours, local_min)

def calculate_linear(diffTime, _from, _to, totaltime):
    return _from + ( (diffTime * (_to - _from)) / totaltime)



def calculate_gamma_values(sunriseTime,sunsetTime, now):
    day_red,   day_green,   day_blue   = [float(x) for x in args.gamma_day.split(":")]
    night_red, night_green, night_blue = [float(x) for x in args.gamma_night.split(":")]
    nowTime = now.hour * 3600 +  now.minute * 60 + now.second
    diffTimeSunrise = nowTime - sunriseTime
    diffTimeSunset = nowTime - sunsetTime
    if abs(diffTimeSunrise) < abs(diffTimeSunset):
        if abs(diffTimeSunrise) > half_transition_time:
            return args.gamma_day if diffTimeSunrise > 0 else args.gamma_night
        else:
            red = calculate_linear(diffTimeSunrise + half_transition_time, night_red, day_red, total_transition_time)
            green = calculate_linear(diffTimeSunrise + half_transition_time, night_green, day_green, total_transition_time)
            blue = calculate_linear(diffTimeSunrise + half_transition_time, night_blue, day_blue, total_transition_time)
            return ":".join([str(round(x,3)) for x in [red, green, blue]])

    else:
        if abs(diffTimeSunset) > half_transition_time: 
            return args.gamma_night if diffTimeSunset > 0 else args.gamma_day
        else:
            red = calculate_linear(diffTimeSunset + half_transition_time, day_red, night_red, total_transition_time)
            green = calculate_linear(diffTimeSunset + half_transition_time, day_green, night_green, total_transition_time)
            blue = calculate_linear(diffTimeSunset + half_transition_time, day_blue, night_blue, total_transition_time)
            return ":".join([str(round(x,3)) for x in [red, green, blue]])

def calculate_brightness(sunriseTime,sunsetTime, now):
    brightness_day   = float(args.brightness_day)
    brightness_night = float(args.brightness_night)
    nowTime = now.hour * 3600 +  now.minute * 60 + now.second
    diffTimeSunrise = nowTime - sunriseTime
    diffTimeSunset = nowTime - sunsetTime
    if abs(diffTimeSunrise) < abs(diffTimeSunset):
        if abs(diffTimeSunrise) > half_transition_time:
            return brightness_day if diffTimeSunrise > 0 else brightness_night
        else:
            return round(calculate_linear(diffTimeSunrise + half_transition_time, brightness_night, brightness_day, total_transition_time), 3)
    else:
        if abs(diffTimeSunset) > half_transition_time: 
            return brightness_night if diffTimeSunset > 0 else brightness_day
        else:
            return round(calculate_linear(diffTimeSunset + half_transition_time, brightness_day, brightness_night, total_transition_time), 3)


coordinates = from_ISO_6709(args.coordinates)
coords = {'longitude' : float(coordinates.longitude.decimal), 'latitude' : float(coordinates.latitude.decimal) }
sunrise = sun.getSunriseTime( coords )
if sunrise['status']:
    sunrise = to_time_in_current_timezone(sunrise)
    sunset = to_time_in_current_timezone(sun.getSunsetTime( coords ))
    now = datetime.datetime.now()
    gamma_values = calculate_gamma_values(sunrise,sunset, now)
    brightness_value = calculate_brightness(sunrise,sunset, now)
else:
    gamma_values = args.gamma_day if sunrise['alwaysDay'] else args.gamma_night
    brightness_value = args.brightness_day if sunrise['alwaysDay'] else args.brightness_night
print('{0} {1}'.format(gamma_values, brightness_value))

