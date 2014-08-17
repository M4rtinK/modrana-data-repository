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
# the compressed planet file download from the Internet needs to
# be at least this big
PLANET_SANITY_THRESHOLD = 20 * GiB

# the planet file split to (uncompressed) continents needs to
# be at least this big
PLANET_SPLIT_SANITY_THRESHOLD = 45 * GiB

# the total size of the continents and all other split areas
# (uncompressed) needs to be at least this big
CONTINENT_SPLIT_SANITY_THRESHOLD = 120 * GiB

PLANET_SPLIT_FOLDER = "split"
PLANET_SPLIT_FOLDER_PATH = os.path.join(PLANET_FOLDER_PATH, PLANET_SPLIT_FOLDER)

# monav routing data should be at least this big
MONAV_RESULTS_SANITY_THRESHOLD = 120 * GiB