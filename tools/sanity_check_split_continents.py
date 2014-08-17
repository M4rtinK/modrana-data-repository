import constants
import utils

# planet & continent split sanity checking

print("= sanity checking the split planet & split continents =")
sane = True
planet_split_size_bytes = 0

try:
    planet_split_size_bytes = utils.get_files_in_folder_size(constants.PLANET_SPLIT_FOLDER_PATH)
except OSError:
    planet_split_size_bytes = 0

print("planet & continent split size: %s" % utils.bytes2PrettyUnitString(planet_split_size_bytes))
print("planet & continent split size sanity threshold: %s" % utils.bytes2PrettyUnitString(constants.CONTINENT_SPLIT_SANITY_THRESHOLD))

if planet_split_size_bytes >= constants.CONTINENT_SPLIT_SANITY_THRESHOLD:
    print("= planet continent split sanity check: OK =")
    exit()
else:
    print("= planet continent split sanity check: NOK =")
    exit(1)