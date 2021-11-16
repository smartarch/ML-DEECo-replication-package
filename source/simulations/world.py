import random
from source.components.bird import Bird
from source.components.drone import DroneState,Drone
from source.components.point import Point
from source.components.field import Field
from source.components.charger import Charger
from source.components.component import Component


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

    # static
    Width = 100
    Height = 100

    droneRadius: int
    def createComponenets(self,targetClassName,points):
        """
            creates instances of type target class name in the size of points
            adds to corresponding list inside the instance
        """
        for point in points:
            targetClass = CLASSNAMES[targetClassName]
            newComponenet = targetClass(point, radius=self.droneRadius)
            self.__dict__[targetClassName].append(newComponenet)
        return self.__dict__[targetClassName]
    

    def __init__(self,conf_dict):
        """
            initiate a world with a YAML configuration file
            component:X a number or list of points for given component

        """
        self.maxSteps = conf_dict['maxSteps']
        conf_dict['maxSteps'] =None
        
        self.mapWidth = conf_dict['mapWidth']
        conf_dict['mapWidth'] =None
        World.Width = self.mapWidth

        self.mapHeight = conf_dict['mapHeight']
        conf_dict['mapHeight'] =None
        World.Height = self.mapHeight
        
        self.droneRadius = conf_dict['droneRadius']
        conf_dict['droneRadius'] =None


        self.drones = []
        self.birds =[]
        self.chargers= []
        self.fields = []
        self.map = {} 

        Component.World = self
        Field.World = self

        for conf,conf_value in conf_dict.items():
            if conf_value is not None:
                points = []
                if isinstance(conf_value,int):
                    for i in range(conf_value):
                        points.append([random.randint(0,self.mapWidth-1), random.randint(0,self.mapHeight-1)])
                else:
                    points = conf_value
                    
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
