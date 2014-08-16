#!/bin/sh

if [ -z "$OSMOSIS_PATH" ]
then
    OSMOSIS=osmosis
else
    OSMOSIS=$OSMOSIS_PATH
fi
echo "path to osmosis:"
echo $OSMOSIS_PATH

PLANET=../planet/planet-latest.osm.pbf
POLYS=../tools/polys/
OUT="compress=none planet/split/"
BUFFER="--buffer bufferCapacity=100000"

sh $OSMOSIS --read-pbf-fast $PLANET --tee 8 ${BUFFER} --bp file=${POLYS}africa.poly ${BUFFER} --write-pbf ${OUT}africa.osm.pbf ${BUFFER} --bp file=${POLYS}antarctica.poly ${BUFFER} --write-pbf ${OUT}antarctica.osm.pbf ${BUFFER} --bp file=${POLYS}asia.poly ${BUFFER} --write-pbf ${OUT}asia.osm.pbf ${BUFFER} --bp file=${POLYS}australia-oceania.poly ${BUFFER} --write-pbf ${OUT}australia-oceania.osm.pbf ${BUFFER} --bp file=${POLYS}central-america.poly ${BUFFER} --write-pbf ${OUT}central-america.osm.pbf ${BUFFER} --bp file=${POLYS}europe.poly ${BUFFER} --write-pbf ${OUT}europe.osm.pbf ${BUFFER} --bp file=${POLYS}north-america.poly ${BUFFER} --write-pbf ${OUT}north-america.osm.pbf ${BUFFER} --bp file=${POLYS}south-america.poly ${BUFFER} --write-pbf ${OUT}south-america.osm.pbf
