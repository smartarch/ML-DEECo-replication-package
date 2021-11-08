# Instructions to configure simulation and YAML configure files.
## YAML Configure File


### __Components__:
#### Components can be set in random bulk or a defined list. To define a bulk of random N components, use N as integer.
#### for example if 10 random drones needed, state as - drones: 10. Alternatively, a list of points can be send to define the initial location of a component. For example the following will initiate 3 drones:
* `drones: [[0.4, 0.5], [0.7,0.2], [0.1,0.7]]`
#### for writing fields, 2 points must be indicated as [top-left and bottom-right], formally defined as [x1, y1, x2, y2] look at the below example:
* `fields: [ [0.1,0.2,0.3,0.4], [0.4,0.6,0.5,0.7] ]`
#### The rest of the configuration is as below:
* 'drones': a positive integer or a list of points.
* 'fields':  a positive integer or a list of pair of points.
* 'birds': a positive integer or a list of points.
* 'charges': a positive integer or a list of points.

### __Max Time Steps__: indicates the maximum time steps of the simulation
* 'maxTimeSteps': a positive integers > 0.

### __Grid Cell Size__: a pair of (Width,Height) rates that represent size of a grid cell on map
* 'gridCellSize': [width,height]


### A YAML configure example
```yaml
drones: 3
birds: 10
chargers: [
  [0.7, 0.1],
  [0.6, 0.5]
]
fields: [
[0.4,0.5,0.7,0.8],
[0.2,0.6,0.3,0.5],
[0.8,0.4,0.9,0.5]
]
maxTimeSteps: 100
gridCellSize: 0.01
```
## Running the simulation
simply run `python run ../experiments/[yamlfile.yaml]`
if no yaml file is selected it will run the default configuration.

