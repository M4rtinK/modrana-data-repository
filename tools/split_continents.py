#/usr/bin/python
#
# Split individual continents as described by regional
# *.poly files. This script does not do the actually
# splitting, just generates arguments for osmosis and
# runs it.

import os
import sys
import subprocess

# make sure relative paths work correctly
# if the script is called from different directory
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

POLY_DIR = "polys"

# path to dir where continental extracts are stored
CONTINENT_PBF_DIR = "../planet/split"

# set output directory
OUT_DIR = "../planet/split"
if len(sys.argv) >= 2:
    OUT_DIR = sys.argv[1]

print("continent splitter initiated")
# check if alternative path to the osmosis
# binary has been specified
OSMOSIS = os.environ.get("OSMOSIS_PATH", "osmosis")
print("path to Osmosis binary: %s" % OSMOSIS)

# process all continents in sequence
# TODO: optionally do all continents at once ?

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
    print("processing continent %s" % continent_name)
    continent_pbf = os.path.join(CONTINENT_PBF_DIR, continent_name, ".pbf")
    args = [OSMOSIS,"-v", "--read-pbf", continent_pbf]
    polygons = []
    # recursively parse all polygon files for the given continent

    def add_poly(path):
        # only add files with .poly extension
        if os.path.splitext(path)[1].lower() == ".poly":
            polygons.append(path)

    def add_region(source, destination):
        args.extend(["--buffer", "--bp", "file=%s" % source,
                    "--buffer", "--write-pbf", "%s" % destination])

    for root, dir, files in os.walk(continent):
        for file in files:
            add_poly(os.path.join(continent, root, file))

    poly_count = len(polygons)
    args.extend(["--tee", str(len(polygons))]) # add number of pipes
    # add source & destination for each polygon
    for poly_path in polygons:
        pbf_path = "%s.osm.pbf" % os.path.splitext(poly_path)[0]
        # remove the "polys" prefix
        # (split by path separator, drop first item, rejoin)
        pbf_path = os.path.join(*os_path_split_full(pbf_path)[1:])
        # add the output folder prefix
        pbf_path = os.path.join(OUT_DIR, pbf_path)
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
    # print("%s" % args)
    print("running Osmosis")
    print("return code: %d" % subprocess.call(args))

print("all done")