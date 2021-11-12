from source.components.agent import Agent
from source.components.charger import Charger
from source.components.field import Field
from source.components.component import Component
from source.components.point import Point
from enum import Enum
import random
import math

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
    MOVING_FIELD = 2
    MOVING_CHARGER = 3
    CHARGING = 4
    TERMINATED = 5
   
class Drone(Agent):
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
    ChargingAlert = 0.1

    def __init__ (
                    self, 
                    location,
                    speed=1,
                    energy=0.005):

        Drone.Count = Drone.Count + 1
        Agent.__init__(self,location,speed,Drone.Count)
        
        #self.location = location
        self.battery = 1 - (0.1 * random.random())
        self.state = DroneState.IDLE
        self.target = None
        self.energy = energy
        self.radius = 5 # 5 points around it
        self.targetFieldPosition = None
        self.targetCharger = None

    def actuate(self):
        self.battery -= self.energy
        if self.battery<=0:
            self.state = DroneState.TERMINATED

        if self.state == DroneState.IDLE or self.state == DroneState.PROTECTING:
            if self.criticalBattery():
                if self.targetCharger!=None:
                    self.target = self.targetCharger.location
                    self.state = DroneState.MOVING_CHARGER
                else:
                    pass
            else:
                self.target = self.targetFieldPosition
                self.state = DroneState.MOVING_FIELD

        if self.state == DroneState.MOVING_CHARGER:
            if self.targetCharger!=None:
                if self.location == self.target:
                    self.state = DroneState.CHARGING
                else:
                    self.move(self.target)
            else:
                pass

        if self.state == DroneState.MOVING_FIELD:
            if self.targetFieldPosition!=None:
                if self.location == self.target:
                    self.state = DroneState.PROTECTING
                else:
                    self.move(self.target)
            else:
                pass
            
        if self.state == DroneState.CHARGING:
            self.targetCharger.charge(self)
            if self.battery >=1 :
                self.state = DroneState.IDLE

    
    def criticalBattery (self):
        return self.battery -  self.energyNeededToMoveToCharger() < Drone.ChargingAlert

    def protectRadius(self):
        startX = self.location[0]-self.radius
        endX = self.location[0]+self.radius
        startY = self.location[1]-self.radius
        endY = self.location[1]+self.radius
        startX = 0 if startX <0 else startX
        startY = 0 if startY <0 else startY
        endX = Component.World.Width-1 if endX>=Component.World.Width else endX
        endY = Component.World.Height-1 if endY>=Component.World.Height else endY
        return (startX,startY,endX,endY)
    
    # return all points that are protected by this drone 
    def locationPoints(self):
        startX,startY,endX,endY = self.protectRadius()
        points = []
        for i in range(startX,endX):
            for j in range(startY,endY):
                points.append([i,j])
        return points

    def energyNeededToMoveToCharger(self):
        if self.targetCharger==None:
            return 0
        p1 = self.location
        p2 = self.targetCharger.location
        distance = math.sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2) )
        energyRequired = distance* self.energy
        return energyRequired


    def __str__ (self):
        return f"id:{self.id},battery:{self.battery},status:{self.state},location:({self.location})"

