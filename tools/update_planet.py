#!/usr/bin/python
import os

import constants

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
    os.remove(constants.PLANET_PATH)
except OSError:
    pass
# download the new one with wget
print("downloading new planet file")
download_rc = os.system("wget %s -P %s" % (constants.PLANET_URL, constants.PLANET_FOLDER_PATH))
print("planet file update done")
exit(download_rc)