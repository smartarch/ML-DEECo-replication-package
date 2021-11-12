from source.components.component import Component
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
                    location):
                
        Charger.Count = Charger.Count + 1
        Component.__init__(self,location,Charger.Count)
        self.rate = 0.02
    
    def charge(self,drone):
        drone.battery = drone.battery + self.rate

    def __str__ (self):
        return f"{self.id},{self.location}"
  