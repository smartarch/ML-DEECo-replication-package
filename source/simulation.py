import base
import tasks
import random

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
    
    

            
class Simulation:
    def run (self):
        # detailed steps
        # create a blank list of components
        components = []
        components.extend(currentWorld.birds)
        components.extend(currentWorld.drones)
        components.extend(currentWorld.chargers)

        chargerEnsembles = []
        for charger in currentWorld.chargers:
            chargerEnsembles.append (tasks.ChargerAssignment(charger))

        fieldProtectionEnsembles= []
        for drone in currentWorld.drones:
            fieldProtectionEnsembles.append (tasks.FieldProtection(drone))

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