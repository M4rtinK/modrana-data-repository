#!/usr/bin/python
import os
import time
import datetime
from subprocess import call

def prettyTimeDiff(dtSeconds):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    diff = datetime.timedelta(seconds=dtSeconds)
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 60:
            return str(second_diff) + " seconds"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours"
    if day_diff < 7:
        return str(day_diff) + " days"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks"
    if day_diff < 365:
        return str(day_diff / 30) + " months"
    return str(day_diff / 365) + " years"

print("starting modRana repository source data update")
start=time.time()
print("updating the planet osm file")
#os.system("./tools/update_planet.sh")
dt = int(time.time() - start)
print("planet osm file update finished in %s" % prettyTimeDiff(dt))

print("splitting the planet into continent sized chunks")
start1=time.time()
os.system("tools/split_planet.sh>split_planet.log")
dt = int(time.time() - start1)
print("planet splitting finished in %s" % prettyTimeDiff(dt))

print("splitting the continents into regions")
start2=time.time()
os.system("tools/split_continents.py>split_continents.log")
dt = int(time.time() - start2)
print("continent splitting finished in %s" % prettyTimeDiff(dt))

dt = int(time.time() - start)
print("source data update finished in %s" % prettyTimeDiff(dt))