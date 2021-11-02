from .base import *
import random

CLASSNAMES = {
    'drones': Drone,
    'birds': Bird,
    'chargers': Charger,
    'places':Place,
}

class World:
    """
        A world consist of Drones, Birds, Places and Chargers
        It also has a field which is consist of multiple places of internets
    """

    drones : list
    birds : list
    places : list
    charges : list
    field : Field


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
            initiate a world with a JSON configuration file
            component:X a number or list of points for given component

        """
        self.timesteps = conf_dict['time_steps']
        conf_dict['time_steps']  =None

        self.drones = []
        self.birds =[]
        self.chargers= []
        self.places = []

        # creates drones, birds, chargers and places
        for conf,conf_value in conf_dict.items():
            if conf_value is not None:
                points = []
                if isinstance(conf_value,int):
                    for i in range(conf_value):
                        if conf=="places":          # a place 4 random values as pair of points
                            points.append([random.random() for i in range(4)])
                        else:
                            points.append(Point(x=random.random(), y =random.random()))
                else:
                    points = conf_value
                self.createComponenets(conf,points)
    
    def run (self):
        pass

