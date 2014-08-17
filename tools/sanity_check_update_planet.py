import os
import urllib

import constants
import utils

# planet update sanity checking

print("= sanity checking the planet file =")
sane = True
planet_size_bytes = 0
try:
    planet_size_bytes = os.path.getsize(constants.PLANET_PATH)
except OSError:
    planet_size_bytes = 0

# size
print("* planet size check *")
print("planet size: %s" % utils.bytes2PrettyUnitString(planet_size_bytes))
print("planet size sanity threshold: %s" % utils.bytes2PrettyUnitString(constants.PLANET_SANITY_THRESHOLD))
if planet_size_bytes >= constants.PLANET_SANITY_THRESHOLD:
    print("* planet size: OK")
else:
    print("* planet size: NOK")
    sane = False

# md5
print("* md5 check *")
remote_checksum = None
local_checksum = None
if constants.PLANET_MD5_URL:
    remote_checksum = None
    try:
        print("retrieving remote planet file checksum from:\n%s" % constants.PLANET_MD5_URL)
        remote = urllib.urlopen(constants.PLANET_MD5_URL)
        remote_checksum = remote.read().split(" ")[0]
        print("remote checksum retrieved:")
        print(remote_checksum)
    except Exception as e:
        print("ERROR: retrieving remote md5 checksum failed")
        print(e)

    # it only makes sense to compute the local checksum if we have the remote checksum
    if remote_checksum:
        try:
            print("computing local md5 checksum")
            local_checksum = utils.hash_file(constants.PLANET_PATH)
            print("local md5 checksum done:")
            print(local_checksum)
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
    print("= planet update sanity check: OK =")
    exit()
else:
    print("= planet update sanity check: NOK =")
    exit(1)