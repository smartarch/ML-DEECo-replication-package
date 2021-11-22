import os
from datetime import date
import random

from common.components import Agent, Bird, Drone, Point, Field, Charger, Component
from common.tasks import PrivateChargerAssignment ,FieldProtection
from common.serialization import Monitor, Report
from common.visualizers import Visualizer

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

    MAX_RANDOMPOINTS = 100
 
    def createComponenets(self,targetClassName,points):
        """
            creates instances of type target class name in the size of points
            adds to corresponding list inside the instance
        """
        for point in points:
            targetClass = CLASSNAMES[targetClassName]
            newComponenet = targetClass(point,self)
            self.__dict__[targetClassName].append(newComponenet)
        return self.__dict__[targetClassName]
    

    def __init__(self,confDict):
        """
            initiate a world with a YAML configuration file
            component:X a number or list of points for given component

        """
        self.maxSteps= 500
        self.mapWidth= 100
        self.mapHeight= 100
        self.droneRadius= 5
        self.birdSpeed= 1 
        self.droneSpeed= 1
        self.droneMovingEnergyConsumption= 0.01
        self.droneProtectingEnergyConsumption= 0.005
        self.chargingRate= 0.2
        self.chargerCapacity= 1
        
        for conf,confValue in confDict.items():
            if conf not in CLASSNAMES:
                self.__dict__[conf] = confValue

        
        self.drones = []
        self.birds =[]
        self.chargers= []
        self.fields = []

        for conf,confValue in confDict.items():
            if conf in CLASSNAMES:
                points = []
                if isinstance(confValue,int):
                    for i in range(confValue):
                        points.append([random.randint(0,self.mapWidth-1), random.randint(0,self.mapHeight-1)])
                else:
                    points = confValue
                    
                createdComponents = self.createComponenets(conf,points)

        self.emptyPoints = []
        for i in range(World.MAX_RANDOMPOINTS):
            p = Point.random(0, 0, self.mapWidth, self.mapHeight)
            if self.isPointField(p):
                i = i - 1
            else:
                self.emptyPoints.append(p)

            
    def isProtectedByDrone(self,point):
        for drone in self.drones:
            if drone.isProtecting(point):
                return True
        return False


    def isPointField(self,point):
        for field in self.fields:
            if field.isPointOnField(point):
                return True
        return False

class Simulation:

    def __init__(self, world, visualize = True):
        self.visualize = visualize
        self.world = world

    def setFieldProtectionEnsembles(self):
        fieldProtectionEnsembles= []
        for field in self.world.fields:
            fieldProtectionEnsembles.append (FieldProtection(field))

        fieldProtectionEnsembles = sorted(fieldProtectionEnsembles, key=lambda x: -x.size())
        totalDrones = len(self.world.drones) - len(fieldProtectionEnsembles)
        circularIndex = 0
        for i in range(totalDrones):
            totalDrones = fieldProtectionEnsembles[circularIndex].assignCardinality(1)
            circularIndex = (circularIndex+1) % len(fieldProtectionEnsembles)

        instantiatedEnsembles = []
        for ens in fieldProtectionEnsembles:
            if ens.materialize(self.world.drones, instantiatedEnsembles):
                instantiatedEnsembles.append(ens)

        return instantiatedEnsembles

    def setPrivateChargers(self):
        privateChargers = []
        for drone in self.world.drones:
            privateChargers.append (PrivateChargerAssignment(drone))
        
                
        instantiatedEnsembles = []
        for ens in privateChargers:
            if ens.materialize(self.world.chargers, instantiatedEnsembles):
                instantiatedEnsembles.append(ens)

        return instantiatedEnsembles

    def run (self):
        elements= []
        
        elements.extend(self.world.drones)
        elements.extend(self.world.birds)
        elements.extend(self.world.chargers)
        elements.extend(self.setFieldProtectionEnsembles())
        elements.extend(self.setPrivateChargers())
        agentReporter = Report(Agent)
        worldReporter = Report(Monitor)

        monitor = Monitor()

        if self.visualize:
            visualizer = Visualizer (self.world)
            visualizer.drawFields()
        
        #instantiatedEnsembles = self.setFieldProtectionEnsembles()
        #instantiatedEnsembles.extend(self.setPrivateChargers())

        for i in range(self.world.maxSteps):
            for element in elements:
                element.actuate()
                if self.visualize:
                    element.report(i)
                
            # for charger in self.world.chargers:
            #     charger.actuate()

            # for ens in instantiatedEnsembles:
            #     ens.actuate()
            
            monitor.report(i,self.world)
            if self.visualize:
                visualizer.drawComponents(i+1)
        
        folder = "results"
        if not os.path.exists(folder):
            os.makedirs(folder)

        today = date.today().strftime("%Y%m%d")
        
        if self.visualize:
            visualizer.createAnimation(f"{folder}/simulation-{today}.gif")

        agentReporter.export(f"{folder}/agents-{today}.csv")
        worldReporter.export(f"{folder}/world-{today}.csv")

       
  


