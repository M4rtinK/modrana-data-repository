# repository tools constants
import os

PLANET_FOLDER = "planet"
PLANET_FOLDER_PATH = os.path.abspath(PLANET_FOLDER)
PLANET_FILENAME = "planet-latest.osm.pbf"
PLANET_PATH = os.path.abspath(os.path.join(PLANET_FOLDER, PLANET_FILENAME))
# located in Europe, good speed, updated weekly
PLANET_URL = "http://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf"
PLANET_MD5_URL = "http://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf.md5"
GiB = 1024 * 1024 * 1024
PLANET_SANITY_THRESHOLD = 20 * GiB