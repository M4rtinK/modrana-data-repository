#!/usr/bin/python
#
# Split individual continents as described by regional
# *.poly files. This script does not do the actually
# splitting, just generates arguments for osmosis and
# runs it.

import os
import time
import traceback
import subprocess
import argparse
import sys

import utils

# make sure relative paths work correctly
# if the script is called from different directory
ABSPATH = os.path.abspath(__file__)
DNAME = os.path.dirname(ABSPATH)
os.chdir(DNAME)

POLY_DIR = "polys"

# path to dir where continental extracts are stored
CONTINENT_PBF_DIR = "../planet/split"

BUFFER_CAPACITY = 10000  # number of nodes to buffer in RAM before writing
BUFFER_SIZE_OVERRIDE = {
    "continent": {
        "europe": 10000 # Europe has many regions, we might sometimes
        # need to use a smaller buffer
    }
}

def get_buffer_size(some_continent, region_count):
    # get override from the override dictionary
    buffer_size = BUFFER_CAPACITY
    override = BUFFER_SIZE_OVERRIDE["continent"].get(some_continent)
    if override:
        buffer_size = override
    # or use smaller buffer if there area many regions
    elif region_count > 80:
        buffer_size = 1000

    return "bufferCapacity=%d" % buffer_size

# set output directory
DEFAULT_OUT_DIR = "../planet/split"

parser = argparse.ArgumentParser(description="Split continents to regions")
parser.add_argument("-o", "--out", help="output dir", type=str, default=DEFAULT_OUT_DIR, dest="out")
parser.add_argument("-c", "--continent", help="split only this continent (subfolder name)",
                    type=str, action="append", default=[], dest="continents")
parser.add_argument("--dry-run", help="don't actually run Osmosis", default=False,
                    dest="dry_run", action="store_true")
parser.add_argument("-v", help="verbose", default=False, dest="verbose", action="store_true")
parser.add_argument("--show-args", help="show the generated Osmosis commandline args",
                    default=False, dest="show_args", action="store_true")

args = parser.parse_args()

print("continent splitter initiated")
startTime = time.time()
# check if alternative path to the osmosis
# binary has been specified
OSMOSIS = os.environ.get("OSMOSIS_PATH", "osmosis")
print("path to Osmosis binary: %s" % OSMOSIS)

# process all continents in sequence
# TODO: optionally do all continents at once ?

#return code
rc = 1

continents = map(lambda x: os.path.join(POLY_DIR, x), os.listdir(POLY_DIR))
# leave only folders (they contain regional polygons)
continents = [c for c in continents if os.path.isdir(c)]
print("%d continents detected:" % len(continents))
continent_names = [os.path.basename(f) for f in continents]
print(", ".join(continent_names))


def os_path_split_full(path):
    parts = []
    while True:
        new_path, tail = os.path.split(path)
        if new_path == path:
            assert not tail
            if path: parts.append(path)
            break
        parts.append(tail)
        path = new_path
    parts.reverse()
    return parts


for continent in continents:
    continent_name = os.path.basename(continent)

    # check for processing overrides
    if args.continents:
        # only split continents requested from cli
        if not continent_name in args.continents:
            continue

    print("processing continent %s" % continent_name)
    continent_pbf = os.path.join(CONTINENT_PBF_DIR, "%s.osm.pbf" % continent_name)
    continent_pbf = os.path.abspath(continent_pbf)
    if args.verbose:
        osmosis_args = [OSMOSIS, "-v", "-q", "1"]
    else:
        osmosis_args = [OSMOSIS]
    osmosis_args.extend(["--read-pbf-fast", continent_pbf])
    polygons = []
    # recursively parse all polygon files for the given continent

    def add_poly(path):
        # only add files with .poly extension
        if os.path.splitext(path)[1].lower() == ".poly":
            polygons.append(path)


    for root, d, files in os.walk(continent):
        for f in files:
            add_poly(os.path.join(root, f))

    poly_count = len(polygons)
    osmosis_args.extend(["--tee", str(poly_count)]) # add number of pipes

    def add_region(source, destination):
        buffer_size = get_buffer_size(continent_name, poly_count)
        osmosis_args.extend(["--buffer", buffer_size, "--bp", "clipIncompleteEntities=true",
                             "file=%s" % source,
                             "--buffer", buffer_size, "--write-pbf", "compress=none",
                             "%s" % destination])

        # --clipIncompleteEntities=false -> clip ways referencing to
        # nodes outside the bounding polygon (Geofabrik does this)
        # TODO: investigate how long would --completeWays=true take
        #       ang how would it behave

    # add source & destination for each polygon
    for poly_path in polygons:
        pbf_path = "%s.osm.pbf" % os.path.splitext(poly_path)[0]
        # remove the "polys" prefix
        # (split by path separator, drop first item, rejoin)
        pbf_path = os.path.join(*os_path_split_full(pbf_path)[1:])
        # add the output folder prefix
        pbf_path = os.path.join(args.out, pbf_path)
        # convert to absolute path, or else makedirs
        # (or possible other utilities ?)
        pbf_path = os.path.abspath(pbf_path)
        poly_path = os.path.abspath(poly_path)
        # make sure the pfb folder exists
        dir_path = os.path.dirname(pbf_path)
        try:
            os.makedirs(os.path.dirname(pbf_path))
        except os.error:
            # folder exists or can't be created
            pass

        add_region(poly_path, pbf_path)

    print("Osmosis arguments generated (%d regions)" % poly_count)
    if args.show_args:
        print("Osmosis args:")
        print(" ".join(osmosis_args))
    if args.dry_run:
        print("not running Osmosis (dry run)")
    else:
        print("running Osmosis")
        try:
            rc = subprocess.call(osmosis_args)
            # if on of the runs failed, skip the rest and return non-zero return code
            if rc > 0:
                print("osmosis run returned non-zero returns code, aborting")
                break
        except Exception:
            print("running osmosis failed:")
            traceback.print_exc(file=sys.stdout)
        print("return code: %d" % rc)

dt = time.time() - startTime
print("splitting finished in %s (%d seconds)" % (utils.prettyTimeDiff(dt), int(dt)))
print("continent splitting done")
exit(rc)