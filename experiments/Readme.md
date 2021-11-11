# Instructions to run the simulation with YAML configure files.
## YAML Configure File


### __Components__:
#### Components can be set in random bulk or a defined list. To define a bulk of random N components, use N as integer.
#### for example if 10 random drones needed, state as - drones: 10. Alternatively, a list of points can be send to define the initial location of a component. For example the following will initiate 3 drones:
* `drones: [[40, 50], [70,25], [11,18]]`

#### The rest of the configuration is as below:
* __drones__: a positive integer or a list of points.
* __birds__: a positive integer or a list of points.
* __charges__: a positive integer or a list of points.

### __Fields__:
#### for writing fields, 2 points must be indicated as [top-left and bottom-right], formally defined as [x1, y1, x2, y2] look at the below example:
* `fields: [ [10,20,30,40], [45,66,55,68] ]`
* __fields__:  a positive integer or a list of pair of points.

### __Max Time Steps__: indicates the maximum time steps of the simulation
* __maxSteps__: a positive integers > 0.

### __Height and Width__: integers that represent the maximum height and width of a map.
* __mapWidth__: a positive integers > 0.
* __mapHeight__: a positive integers > 0.

### A YAML configure example
```yaml
drones:  [ 
  [17,45],
  [22,12],
  [90,85]
]
birds: 8
chargers: [
  [45,77],
  [65,19]
]
fields: [
  [20,10,45,25],
  [20,60,40,80],
  [81,35,90,44]
]
maxSteps: 1000
mapWidth: 100
mapHeight: 100
```
## Running the simulation
simply run `python source\run.py experiments\exp1.yaml`
* if no yaml file is selected it will run the default configuration.


## Results
the results will be save in the run location under the folder named __results__, and it currently has:
* animation video in GIF format
* agent report in CSV format