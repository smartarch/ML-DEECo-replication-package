

import random
import numpy as np
from datetime import date
from matplotlib import pyplot as plt
from components import Bird, Drone, Charger,Field, Point
from tasks import ChargerAssignment , FieldProtection
from serializer import Report
currentWorld = None

CLASSNAMES = {
    'drones': Drone,
    'birds': Bird,
    'chargers': Charger,
    'fields':Field,
}


class World:
    """
        A world class consist of Drones, Birds, Fields and Chargers.
    """

    drones : list
    birds : list
    charges : list
    field : list
    gridSize: int
    maxSteps: int
    mapWidth : int
    mapHeight : int

    def createComponenets(self,targetClassName,points):
        """
            creates instances of type target class name in the size of points
            adds to corresponding list inside the instance
        """
        for point in points:
            targetClass = CLASSNAMES[targetClassName]
            newComponenet = targetClass(point)
            self.__dict__[targetClassName].append(newComponenet)

    

    def __init__(self,conf_dict):
        """
            initiate a world with a YAML configuration file
            component:X a number or list of points for given component

        """
        self.maxSteps = conf_dict['maxSteps']
        conf_dict['maxSteps'] =None

        self.gridSize = conf_dict['gridSize']
        conf_dict['gridSize'] =None
        
        self.mapWidth = conf_dict['mapWidth']
        conf_dict['mapWidth'] =None
        
        self.mapHeight = conf_dict['mapHeight']
        conf_dict['mapHeight'] =None

        self.drones = []
        self.birds =[]
        self.chargers= []
        self.fields = []
        
        # creates drones, birds, chargers and fields
        for conf,conf_value in conf_dict.items():
            if conf_value is not None:
                points = []
                if isinstance(conf_value,int):
                    for i in range(conf_value):
                        points.append(Point(x=random.randint(0,self.mapWidth), y =random.randint(0,self.mapHeight)))
                else:
                    points = conf_value
                self.createComponenets(conf,points)


class Simulation:

    def run (self):
        birds = currentWorld.birds
        birdReport = Report(Bird)
        
        for i in range(currentWorld.maxSteps):
            for bird in birds:
                bird.actuate()
                bird.report(i)


        today = date.today().strftime("%Y%m%d")
        birdReport.export(f"../experiments/results/birds-{today}.csv")

    def run1 (self):
        # detailed steps
        # create a blank list of components
        components = []
        components.extend(currentWorld.birds)
        components.extend(currentWorld.drones)
        components.extend(currentWorld.chargers)

        """
            according to the chargers
        """
        chargerEnsembles = []
        for charger in currentWorld.chargers:
            chargerEnsembles.append (ChargerAssignment(charger))

        """
            according to fields
        """
        fieldProtectionEnsembles= []
        for field in currentWorld.fields:
            fieldProtectionEnsembles.append (FieldProtection(field))

        # in cases the priority is considered such as we say protecting > patroling
        # TODO priority might be changed to a different feature
        chargerEnsembles = sorted(chargerEnsembles, key=lambda x: x.priority())

        # TODO know why do we have to materialize ensembles?
        # for ens in potentialEnsembles:
        #     if ens.materialize(components, instantiatedEnsembles):
        #         instantiatedEnsembles.append(ens)
        #         ens.actuate()

        for i in range(currentWorld.maxSteps):
            for component in components:
                component.actuate()
                print (f"{i}: {component}")

