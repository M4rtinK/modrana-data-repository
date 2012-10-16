modRana data repository
=======================

ModRana data repository serves data to users running modRana in the field.

This is basically the server side, the cleint side will be part of modRana itself.
Of course, nothing prohibits other applications being used as cleints, provided they implement the necessary protocol (basically just parsing the repository manifest files).

Monav routing data
----------
Monav routing data are currently the "main user" of mdr, even though its architecture should be flexible enough to handle other arbitrary data bundles.

The repository handles the wholeMonav routing data cycle:
    * download protobuf with current data for an area
    * process protobuf with _mona-preprocessor_
    * compress the resulting car/pedestrian/bicycle data packs
    * publish the packs & update the Monav repository manifest
