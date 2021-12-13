# #import sklearn.metrics as metrics
# import numpy as np
# from sklearn.model_selection import TimeSeriesSplit
# X = np.array([[1, 2], [3, 4], [1, 2], [3, 4], [1, 2], [3, 4]])
# y = np.array([1, 2, 3, 4, 5, 6])
# tscv = TimeSeriesSplit()
# print(tscv)


from yaml import load, dump
import random
from common.charger_waiting_estimation import getChargerWaitingTimeEstimation

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import os
import copy
from common.simulation import World,Simulation
from common.serialization import Log

def run(filename):
    yamlFile = open(filename, 'r')
    yamlObject = load(yamlFile, Loader=Loader)
    
    yamlFileName = os.path.splitext(os.path.basename(filename))[0]
    conf = yamlObject
    world = World(conf)
    
    folder = "results\\time_run"
    if not os.path.exists(folder):
        os.makedirs(folder)


    model = None
    timeLog = Log([
        "maxIterations",
        "dead_rate",
        "charge_alert",
        "average_protecting_time",
        "average_waiting_time",
        "energy_used",
        "damage_rate",
    ])

    for i in range(1000):
        currentWorld = copy.deepcopy(world)
        randomAlert = (random.random() * 0.7) + 0.2
        for drone in currentWorld.drones:
            drone.alert = randomAlert
        newSimulation = Simulation(currentWorld, folder, visualize=False)
        register = newSimulation.timeRun(model,timeLog,500)
    register.export(folder+"\\"+yamlFileName+"_5hk.csv")

if __name__ == "__main__":
    run("experiments\\small.yaml")
