#!/usr/bin/python
import os
import time

from core.utils import prettyTimeDiff, createFolderPath

log_folder = "logs/source_data_update_logs_%s" % time.strftime("%Y.%m.%d-%H:%M:%S")
log_folder = os.path.abspath(log_folder)

# as the source data update can happen independently on the repository update
# it has it's own log folder - it should be easy to correlate which source data
# update was followed by which repository update by the date

if not createFolderPath(log_folder):
    print("ERROR: can't create log folder for the source data update run in:")
    print(log_folder)
    print("log data for this update run might not be gathered or the update run might fail outright")

planet_update_log = os.path.join(log_folder, "update_planet.log")
planet_split_log = os.path.join(log_folder, "split_planet.log")
continents_split_log = os.path.join(log_folder, "split_continents.log")

print("starting modRana repository source data update")
start=time.time()
print("updating the planet osm file")
os.system("./tools/update_planet.sh&>%s" % planet_update_log)
dt = int(time.time() - start)
print("planet osm file update finished in %s" % prettyTimeDiff(dt))

print("splitting the planet into continent sized chunks")
start1=time.time()
os.system("./tools/split_planet.sh&>%s" % planet_split_log)
dt = int(time.time() - start1)
print("planet splitting finished in %s" % prettyTimeDiff(dt))

print("splitting the continents into regions")
start2=time.time()
os.system("./tools/split_continents.py&>%s" % continents_split_log)
dt = int(time.time() - start2)
print("continent splitting finished in %s" % prettyTimeDiff(dt))

dt = int(time.time() - start)
print("source data update finished in %s" % prettyTimeDiff(dt))