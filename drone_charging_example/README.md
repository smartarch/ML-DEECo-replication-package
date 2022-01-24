# Drone charging example

## How to run the example

Install ML-DEECo using `pip` (the `--editable` switch can be omitted if one does plan to change the code of ML-DEECo):

```
pip install --editable ../ml_deeco
```

Run the `run.py` file:

```
py -3 run.py experiments/16drones.yaml -n 1 -t 3 -o 16/nn_test -v 2
```
