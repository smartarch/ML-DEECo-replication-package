"""
    This file contains the base classes and formal defintions for each type that are being dealt with it in the research.\
    The classes are:
        1. Component Class: an abstract class that simply parnets all component objects on the field.
            A. Drone
            B. Charger
            C. Bird

"""
from enum import Enum
from .utility import diff

class Point:
    """
        The class represents a point on the world.
        X and Y are values from 0 to 1, for instance 0.5 meaning at the center of map.
        The default values at the start of each Point is 0.5 and 0.5
        Please keep in mind that the X and Y must be a value, where  0 < value < 1
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
        if value<=0 or value>=1: 
            raise Exception("X must be between (0,1).")
        self._x = value
    
    @property
    def y (self):
        return self._y
    
    @y.setter
    def y(self, value):
        if value<0 or value>1: 
            raise Exception("Y must be between (0,1).")
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

        Static Count for the Fields
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
    target: Point

    # speed of the drone which is distance unit / time unit, default value = 0.01
    speed :float

    # amount of the energy required to live in 1 timestep (rename it later)
    energy :float

    def __init__ (
                    self, 
                    location=Point(),
                    speed=0.01,
                    energy=0.01):

        Drone.Count = Drone.Count + 1
        Component.__init__(self,Drone.Count)
        
        self.location = location
        self.battery = 1
        self.state = DroneState.IDLE
        self.target = None
        self.energy = energy

    ### rename and add comments
    def live (self):
        # if the drone is dead return false
        if self.state == DroneState.TERMINATED:
            return False


        # if the drone is not charging, then decrease the living cost
        if self.state != DroneState.CHARGING:
            self.battery = self.battery - self.energy
            # check if the battery is dead, then change the state of drone
            if self.battery<=0:
                self.state = DroneState.TERMINATED
                return False

        return True
            

    # move the drone for 1 time step
    def moveToPoint (
                        self,
                        target):
        
        if self.live():
            x_forward = self.speed * (utility.diff(self.location.x,target.x))
            y_forward = self.speed * (utility.diff(self.location.y,target.y))
            
            
            self.location.x = self.location.x + x_forward
            self.location.y = self.location.y + y_forward
            return True

        return False


    def energyNeededToStartCharging(self):
        # calculation required
        return 0.15

    # added functions
    def needsCharging(self):
        """
        	Tomas's Comments
            .... initial estimate
      	    .... trained - for this we have a predictor
            .... features: drone.pos, drone.battery, overallDemand on the chargers (number of drones currently in the need of charging), number of available chargers, ....
        
            This property returns true if a drone needs charging or not/
        """

        return self.state is not DroneState.CHARGING and self.battery < self.energyNeededToStartCharging() + 0.05  # <-- what is this?
  

    def __str__ (self):
        print ("%s, battery:%f, status:%d"%(self.id,self.battery,self.state))

class Charger (Component):
    """
        The charger class represnets a charging slot.
        Location: type of a Point (x,y) in a given world.
        Client: a variable to indicate which drone has reserved the time of this charger.
        Rate: the speed (rate) of charging, is basically power unit  / time unit
        Static Count for the Chargers
    """
    # static Counter
    Count = 0

    # the location on the zone/map/field
    location: Point

    # which drone has reserved the Charger
    client: Drone

    # rate of charging per timestep defined as power unit / time unit
    rate : float
    
    def __init__ (
                    self,
                    location, 
                    rate=0.01):
                
        Charger.Count = Charger.Count + 1
        Component.__init__(self,Charger.Count)

        self.location = location
        self.rate = rate
        self.client = None

    def is_busy (self):
        return self.client != None
    """
        need some clarification 
    
    def step(self):
      	if (self.state == IDLE or self.state == PROTECTING) and self.targetCharger is not None:
          	self.state = DroneState.MOVING_TO_CHARGER
        
        if self.state == CHARGING and self.battery == 1:
          	self.targetCharger = None
            self.state = IDLE
    """



class Bird(Component):
    """
        The charger class represnets a bird/flock/imposter.
        Location: type of a Point (x,y) in a given world.
        Center: the center of an area of interest.
        Speed: the speed (rate) of charging, is basically power unit  / time unit
        Static Count for the Birds
    """
    # static Counter
    Count = 0

    # the location on the zone/map/field
    location: Point

    # speed of the bird which is distance unit / time unit, default value = 0.01
    speed :float

    # intrest zone's center,  something to be remembered by bird, where is a good place to visit
    center : Point

    def __init__(
                    self,
                    location,
                    speed=0.01):

        Bird.Count = Bird.Count + 1
        Component.__init__(self,Bird.Count)

        self.location = location
        self.speed = speed