"""
    This file contains the base classes and formal defintions for each type that are being dealt with it in the research.\
    The classes are:
        1. Component Class: an abstract class that simply parnets all component objects on the field.
            A. Drone
            B. Charger
            C. Bird

"""
from enum import Enum

class Point:
    """
        The class represents a point on the world.
        X and Y are values from 0 to 1, for instance 0.5 meaning at the center of map.
        The default values at the start of each Point is 0.5 and 0.5
    """

    _x: float
    _y: float

    def __init__ (
                    self,
                    x=.5,
                    y=.5):
        self.x = x
        self.y = y

    @property
    def x (self):
        return self._x
    
    @x.setter
    def x(self, value):
        if value<0 or value>1: 
            raise Exception("X must be between 0 and 1.")
        self._x = value
    
    @property
    def y (self):
        return self._y
    
    @y.setter
    def y(self, value):
        if value<0 or value>1: 
            raise Exception("Y must be between 0 and 1.")
        self._y = value


class Component:
    """
        The abstract class for the Chargers, Drones, Flocks or any other component lives on the field.
        ID is auto assigned as the TYPE NAME ID  
    """
    id: str
    def __init__(
                    self,
                    id=0):
        child_type = type(self).__name__
        self.id = "%s_%d"%(child_type, id)

class Place(Component):
    """
        This defines an Area, which is technically a set of points.
        Any polygon can be defined as [(x1,y1), (x2,y2), (x3,y3),... (xn,yn)]
        The list of points are defined in local points variable.
    """
    points: list()

    # Static Count
    Count = 0
    def __init__ (
                    self, 
                    points):

        # each Place is given an ID and a TAG: Place
        # for example the first Place object will be Place_1
        Place.Count = Place.Count + 1
        Component.__init__(self,Place.Count)

        self.points = points
    

    def is_inside(
                    self,
                    given_point):

        """
            this function checks if a point is inside the Place or not.
            It returns True if given_point is inside the polygon

            !NOT IMPLEMENTED YET!
        """
        return False

class Field (Component):
    """
        A Field that the simulation is running on.
        The places contain all the places on the Field.
    """

    # Field counter
    Count = 0

    places: list()
    def __init__ (
                    self,
                    places):
        Field.Count = Field.Count + 1
        Component.__init__(self,Field.Count)
    
        self.places = places

    

class DroneState(Enum):
    """
        An enumerate property for the drones.
        IDLE: a default state for drones.
        PROTECTING: when the drones are protecting the zones.
        MOVING_TO_CHARGING: when the drones are moving/queuing for a charger.
        CHARGIN: when the drones are being chareged.
        TERMINATED: when the drone's battery is below 0 and they do not operate anymore.
    """

    IDLE = 0
    PROTECTING = 1
    MOVING_TO_CHARGER = 2
    CHARGING = 3
    TERMINATED = 4


class Drone(Component):
    """
        The drone class represent the active drones that are in the field.
        Location: type of a Point (x,y) in a given world.
        Battery: a level that shows how much of battery is left. 1 means full and 0 means empty.
        State: the state of a Drone as following:
            0 IDLE: a default state for drones.
            1 PROTECTING: when the drones are protecting the zones.
            2 MOVING_TO_CHARGING: when the drones are moving/queuing for a charger.
            3 CHARGIN: when the drones are being chareged.
            4 TERMINATED: when the drone's battery is below 0 and they do not operate anymore.
        Target: is the target component, it could be a place, a charger, a bird, or anything else.
        Static Count for the Drones
    """
    # static Counter
    Count = 0

    # the location on the zone/map/field
    location: Point

    # the rate of battery, 0: empty and 1 means full
    battery: float

    # the state which drone exists in
    state: DroneState

    # target is either a charger or a bird/activity
    targe: Component

    def __init__ (
                    self, 
                    location=Point()):

        Drone.Count = Drone.Count + 1
        Component.__init__(self,Drone.Count)
        
        self.location = location
        self.battery = 1
        self.state = DroneState.IDLE
        self.targe = None



class Charger (Component):
    """
        The charger class represnets a charging slot.
        Location: type of a Point (x,y) in a given world.
        Client: a variable to indicate which drone has reserved the time of this charger.
        Speed: the speed of charging, is basically power unit  / time unit
        Static Count for the Drones
    """
    # static Counter
    Count = 0

    # the location on the zone/map/field
    location: Point

    # which drone has reserved the Charger
    client: Drone

    # rate (speed) of charging per timestep defined as power unit / time unit
    speed : float
    
    def __init__ (
                    self,
                    location, 
                    speed=0.01):
                
        Charger.Count = Charger.Count + 1
        Component.__init__(self,Charger.Count)

        self.location = location
        self.speed = speed
        self.client = None

    def is_busy (self):
        return self.client != None