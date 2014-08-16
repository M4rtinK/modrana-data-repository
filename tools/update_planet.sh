#!/bin/sh
cd ../planet
#echo "running osmupdate"
#osmupdate -v planet-latest.pbf planet-latest-updated.pbf
#echo "replacing old planet file"
rm -f planet-latest.pbf
#mv planet-latest-updated.pbf planet-latest.pbf
wget http://ftp5.gwdg.de/pub/misc/openstreetmap/planet.openstreetmap.org/pbf/planet-latest.osm.pbf
echo "planet update done"
cd ..
