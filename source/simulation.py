import base
import tasks
import random
import math
import numpy as np

from PIL import Image  

currentWorld = None


CLASSNAMES = {
    'drones': base.Drone,
    'birds': base.Bird,
    'chargers': base.Charger,
    'fields':base.Field,
}


class World:
    """
        A world class consist of Drones, Birds, Fields and Chargers.
    """

    drones : list
    birds : list
    charges : list
    field : list
    cellSize: tuple
    maxSteps: int

    places : dict

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
        self.maxSteps = conf_dict['maxTimeSteps']
        conf_dict['maxTimeSteps'] =None

        self.cellSize = conf_dict['gridCellSize']
        conf_dict['gridCellSize'] =None

        self.drones = []
        self.birds =[]
        self.chargers= []
        self.fields = []
        self.places = {}
        # creates drones, birds, chargers and places
        for conf,conf_value in conf_dict.items():
            if conf_value is not None:
                points = []
                if isinstance(conf_value,int):
                    for i in range(conf_value):
                        if conf=="fields":          # a field 4 random values as pair of points
                            points.append([random.random() for i in range(4)])
                        else:
                            points.append(base.Point(x=random.random(), y =random.random()))
                else:
                    points = conf_value
                self.createComponenets(conf,points)



    def generateKey (self,point):
        """
            the point is converted to a string code for better hashing 
            point (0.03,0.040001) is converted to "03-04" key
            Note that the generated key is relative to size of cell
        """
        decimalPlaces = int(math.log(1/self.cellSize,10))
        xPart = str(round(point.x,decimalPlaces))
        yPart = str(round(point.y,decimalPlaces))

        keyStr = f"{xPart}-{yPart}"
        return keyStr
    
    def generatedKey(self,x,y):
        """
            generate keys from integer x and integer y
        """
        keyStr = f"{str(x).zfill(2)}-{str(y).zfill(2)}"
        return keyStr
    
    def unLockKey (self,strKey):
        keyValues = strKey.split('-')
        return float(keyValues[0])*100,float(keyValues[1])*100

    def setPoint (self, point, component):
        """
            places as a component on map
            the place variable is a dictionary
            for example we call the world to set a point to see what is out there
            the value to this is basically a list of componenets meaning what are located there
        """

        # converting a point to a key
        keyStr = self.generateKey(point)
        if keyStr not in self.places:
            self.places[keyStr] = []
        
        self.places[keyStr].append(component)
    
    def checkPoint (self,point):
        """
            to check what component we have on this given point.
            if the point is known on the map, we return a list of components that lives there

        """
        keyStr = self.generateKey(point)
        if keyStr not in self.places:
            return None
        
        return self.place[keyStr]

    def unSetPoint (self,point, component):
        """
            to remove the component from the given point
        """
        keyStr = self.generateKey(point)
        if keyStr in self.places:
            self.places[keyStr].remove(component)
            if len(places[keyStr])==0:
               self.places[keyStr] = None

    def show (self):
        array = np.zeros((int(1.0/self.cellSize),int(1.0/self.cellSize)),dtype=int)
        for place in self.places:
            x,y = self.unLockKey(place)
            array[int(y),int(x)] = 255
        return array

from matplotlib import pyplot as plt

            
class Simulation:
    def run1(self):
        for field in currentWorld.fields:
            field.drawField(currentWorld)
        array = currentWorld.show()
        plt.imshow(array, interpolation='nearest')
        plt.show()
        

    def run (self):
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
            chargerEnsembles.append (tasks.ChargerAssignment(charger))

        """
            according to fields
        """
        fieldProtectionEnsembles= []
        for field in currentWorld.fields:
            fieldProtectionEnsembles.append (tasks.FieldProtection(field))

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