import os
from datetime import date
import random

from common.components import Agent, Bird, Drone, Point, Field, Charger, Component
from common.tasks import FieldProtection, MasterCharger
from common.serialization import Log
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
        self.droneBatteryRandomize= 0
        self.droneMovingEnergyConsumption= 0.01
        self.droneProtectingEnergyConsumption= 0.005
        self.chargingRate= 0.2
        self.chargerCapacity= 1

        self.currentTimeStep = 0
        
        for conf,confValue in confDict.items():
            if conf not in CLASSNAMES:
                self.__dict__[conf] = confValue

        Point.MaxWidth = self.mapWidth
        Point.MaxHeight = self.mapHeight
        
        self.drones = []
        self.birds =[]
        self.chargers= []
        self.fields = []


        for i in range(confDict['drones']):
            point = Point.randomPoint() 
            self.drones.append(Drone(point,self))

        for i in range(confDict['birds']):
            point = Point.randomPoint() 
            self.birds.append(Bird(point,self))

        for chargerPoint in confDict['chargers']:
            for i in range(confDict['chargerCapacity']):
                self.chargers.append(Charger(chargerPoint,self))

        for fieldPoints in confDict['fields']:
            self.fields.append(Field(fieldPoints,self))


        self.sortedFields = sorted(self.fields,key = lambda field : -len(field.places))
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

    def __str__(self):
        return ""

class Simulation:

    def __init__(self, world, visualize = True):
        self.visualize = visualize
        self.world = world

    def setFieldProtectionEnsembles(self):
        fieldProtectionEnsembles= []
        for field in self.world.fields:
            fieldProtectionEnsembles.append (FieldProtection(field,self.world))

        instantiatedEnsembles = []
        for ens in fieldProtectionEnsembles:
            if ens.materialize(self.world.drones, instantiatedEnsembles):
                instantiatedEnsembles.append(ens)

        return instantiatedEnsembles


    def run (self,filename):
        
        elements= []
        
        elements.extend(self.world.drones)
        elements.extend(self.world.birds)
        elements.extend(self.setFieldProtectionEnsembles())

        log = Log()
        masterCharger = MasterCharger(self.world,log)


        if self.visualize:
            visualizer = Visualizer (self.world)
            visualizer.drawFields()
        
        for i in range(self.world.maxSteps):
            self.world.currentTimeStep = i
            for element in elements:
                element.actuate()
 
            masterCharger.actuate()
            if self.visualize:
                visualizer.drawComponents(i+1)
        
        for record in masterCharger.records:
            masterCharger.records[record].append('-')
            log.register(masterCharger.records[record]) 

        folder = "results"
        if not os.path.exists(folder):
            os.makedirs(folder)

        today = date.today().strftime("%Y%m%d")
        
        if self.visualize:
            visualizer.createAnimation(f"{folder}/simulation-{filename}-{today}.gif")

        log.export(f"{folder}/log-{filename}-{today}.csv")
        #agentReporter.export(f"{folder}/agents-{today}.csv")
        #worldReporter.export(f"{folder}/world-{today}.csv")

       
  


