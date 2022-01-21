# EN2 Drone Charging

The project file regarding the ensembles of drones and chargers. 

## How to run the example

Install ML-DEECo

```
cd ml_deeco
pip install --editable .
```

Change directory to the example and run it.

```
cd ../drone_charging_example
py -3 run.py experiments/16drones.yaml -n 1 -t 3 -o 16/nn_test -v 2
```
