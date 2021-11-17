import random
from source.components.bird import Bird
from source.components.drone import Drone
from source.components.point import Point
from source.components.field import Field
from source.components.charger import Charger
from source.components.component import Component

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
        self.droneEnergyMovingConsumption= 0.01
        self.droneEnergyProtectingConsumption= 0.005
        self.chargingRate= 0.2
        for conf,confValue in confDict.items():
            if conf not in CLASSNAMES:
                self.__dict__[conf] = confValue

        
        self.drones = []
        self.birds =[]
        self.chargers= []
        self.fields = []



        self.map = {} 
        self.map
        for conf,confValue in confDict.items():
            if conf in CLASSNAMES:
                points = []
                if isinstance(confValue,int):
                    for i in range(confValue):
                        points.append([random.randint(0,self.mapWidth-1), random.randint(0,self.mapHeight-1)])
                else:
                    points = confValue
                    
                createdComponents = self.createComponenets(conf,points)
                # add the correspoding function to the map of components
                for component in createdComponents:
                    self.map[component] = component.locationPoints()
            


    @property
    def nonEmptyPoints(self):
        return [point for component in self.map for point in self.map[component]]

    @property
    def emptyPoints (self):
        return [[x,y] for x in range(self.mapWidth) for y in range(self.mapHeight) if [x,y] not in self.nonEmptyPoints]



    def components(self,point):
        if isinstance(point, Point):
            return [component for component in self.map if [point.x,point.y] in self.map[component]]
        else:
            return [component for component in self.map if point in self.map[component]]
    
    def isPointField(self,point):
        for field in self.fields:
            if field.isPointOnField(point):
                return True
        return False
