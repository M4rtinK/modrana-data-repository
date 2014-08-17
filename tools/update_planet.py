#!/usr/bin/python
import shutil
import os
import urllib
import hashlib

PLANET_FOLDER = "planet"
PLANET_FILENAME = "planet-latest.pbf"
PLANET_PATH = os.path.join(PLANET_FOLDER, PLANET_FILENAME)
# located in Europe, good speed, updated weekly
PLANET_URL = "http://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf"
PLANET_MD5_URL = "http://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf.md5"
GiB = 1024 * 1024 * 1024
PLANET_SANITY_THRESHOLD = 20 * GiB

def bytes2PrettyUnitString(input_bytes):
    input_bytes = float(input_bytes)
    if input_bytes >= 1099511627776:
        terabytes = input_bytes / 1099511627776
        size = '%.2fTB' % terabytes
    elif input_bytes >= 1073741824:
        gigabytes = input_bytes / 1073741824
        size = '%.2fGB' % gigabytes
    elif input_bytes >= 1048576:
        megabytes = input_bytes / 1048576
        size = '%.2fMB' % megabytes
    elif input_bytes >= 1024:
        kilobytes = input_bytes / 1024
        size = '%.2fKB' % kilobytes
    else:
        size = '%.2fb' % input_bytes
    return size

# osmupdate does transfer only the diffs if you provide it the right timestamp
# but unfortunately takes too much time in the and
# - we can download the whole file much faster
# - maybe try it with uncompressed planet file ?
#
#echo "running osmupdate"
#osmupdate -v planet-latest.pbf planet-latest-updated.pbf
#echo "replacing old planet file"
#mv planet-latest-updated.pbf planet-latest.pbf


print("updating the planet file")

# remove the old planet file
try:
    print("removing the old planet file")
    os.remove(PLANET_PATH)
except OSError:
    pass
# download the new one with wget
print("downloading new planet file")
os.system("wget %s -p %s" % (PLANET_URL, PLANET_PATH))

# some sanity checking

print("= sanity checking the planet file")
sane = True
planet_size_bytes = 0
try:
    os.path.getsize(PLANET_PATH)
except OSError:
    planet_size_bytes = 0

# size
print("* planet size check")
print("planet size: %s" % bytes2PrettyUnitString(planet_size_bytes))
print("planet size sanity threshold: %s" % bytes2PrettyUnitString(PLANET_SANITY_THRESHOLD))
if planet_size_bytes >= PLANET_SANITY_THRESHOLD:
    print("* planet size: OK")
else:
    print("* planet size: NOK")
    sane = False

# md5
print("* md5 check")
remote_checksum = None
local_checksum = None
if PLANET_MD5_URL:
    remote_checksum = None
    try:
        print("retrieving remote planet file checksum from:\n%s" % PLANET_MD5_URL)
        remote = urllib.urlopen(PLANET_MD5_URL)
        remote_checksum = remote.read().split(" ")[0]
        print("remote checksum retrieved")
    except Exception as e:
        print("ERROR: retrieving remote md5 checksum failed")
        print(e)

    # it only makes sense to compute the local checksum if we have the remote checksum
    if remote_checksum:
        try:
            print("computing local md5 checksum")
            local_checksum = hashlib.md5(PLANET_PATH).hexdigest()
            print("local md5 checksum dome")
        except Exception as e:
            print("local md5 checksum computation failed")
            print(e)

if remote_checksum is None or local_checksum is None:
    print("skipping the md5 check - can't get remote or local checksum")
else:
    if remote_checksum == local_checksum:
        print("* md5 checksum: OK")
    else:
        print("* md5 checksum: NOK")
        sane = False

if sane:
    print("planet update finished successfully")
    exit()
else:
    print("planet update failed")
    exit(1)
