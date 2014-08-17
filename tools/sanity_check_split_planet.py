#!/usr/bin/python
import constants
import utils

# planet split sanity checking

print("= sanity checking the split planet file =")
sane = True
planet_split_size_bytes = 0

try:
    planet_split_size_bytes = utils.get_files_in_folder_size(constants.PLANET_SPLIT_FOLDER_PATH)
except OSError:
    planet_split_size_bytes = 0

print("planet split size: %s" % utils.bytes2PrettyUnitString(planet_split_size_bytes))
print("planet split size sanity threshold: %s" % utils.bytes2PrettyUnitString(constants.PLANET_SPLIT_SANITY_THRESHOLD))

if planet_split_size_bytes >= constants.PLANET_SPLIT_SANITY_THRESHOLD:
    print("= planet split sanity check: OK =")
    exit()
else:
    print("= planet split sanity check: NOK =")
    exit(1)