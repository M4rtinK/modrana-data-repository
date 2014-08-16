modRana data repository
=======================

ModRana data repository serves data to users running modRana in the field.

This is basically the server side, the client side will be part of modRana itself.
Of course, nothing prohibits other applications being used as clients, provided they implement the necessary protocol (basically just parsing the repository manifest files).

Dependencies
------------
To effectively run a modRana data repository you need a couple of dependencies:
    * python
    * osmosis (for splitting the planet file to smaller areas)    
    * monav-preprocessor (for generating the Monav routing data)
    * wget (downloading planet updates)
    * osmupdate & osmconvert (for efficiently updating the planet file, optional)
    * tmux (for monitoring/debugging updates manually, optional)    

Monav routing data
------------------
Monav routing data are currently the "main user" of mdr, even though its architecture should be flexible enough to handle other arbitrary data bundles.

The repository handles the wholeMonav routing data cycle:
    * download protobuf with current data for an area
    * process protobuf with _mona-preprocessor_
    * compress the resulting car/pedestrian/bicycle data packs
    * publish the packs & update the Monav repository manifest
