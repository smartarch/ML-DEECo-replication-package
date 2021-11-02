# Instructions to configure simulation and JSON configure files.
## JSON Configure File


* Components:
    Components can be set in random bulk or a defined list. To define a bulk of component as X, just use X as integer
    for example if 10 random drones needed, state as "drones":10. Alternatively, a list of points can be send to define the initial location of a component. For example the following will initiate 3 drones:
    > drones : [[0.4, 0.5], [0.7,0.2], [0.1,0.7]]
    for writing places, pair of points must be indicated as top-left and bottom-right, look at the below example:
    > places : [ [[0.1,0.2],[0.3,0.4]], [[0.4,0.6],[0.5,0.7]] ]
    The rest of the configuration is as below:
    * 'drones': x where x is a positive integer or a list of points.
    * 'places': x where x is a positive integer or a list of pair of points.
    * 'birds': x where x is a positive integer or a list of points.
    * 'charges': x where x is a positive integer or a list of points.

* Timesteps: any integer that is shown in 
    * 'timesteps': X where x is a positive integers > 0.

## Running the simulation
simply run `python run [jsonfile.json]`
if no json file is selected it will run the default configuration.