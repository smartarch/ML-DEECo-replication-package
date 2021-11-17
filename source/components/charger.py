from source.components.component import Component
from source.components.point import Point
import random

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

    
    def __init__ (
                    self,
                    location,
                    world):
        self.chargingRate = world.chargingRate

        Charger.Count = Charger.Count + 1
        Component.__init__(self,location,world,Charger.Count)
        
        self.occupied = False
        self.client = None
    
    def charge(self,drone):
        if self.client != drone:
            return

        drone.battery = drone.battery + self.chargingRate
        if drone.battery >= 1:
            self.client = None


    def randomLocationClose (self):
        return Point(self.location.x+random.randint(-5,5),self.location.y+random.randint(-5,5))

    def __str__ (self):
        return f"{self.id},{self.location}"
  