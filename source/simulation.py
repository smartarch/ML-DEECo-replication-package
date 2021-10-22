from .base import *
import random

class World:
    drones : list()


    def __init__(self,max_number = 20 ,radnom_seed=23913):
        # random location
        random.seed(radnom_seed)

        # if we want this method to add only as append, we need to omit the following line
        self.drones = list()

        # generate max number drones, and append them to the drones list
        for i in range(0,max_number):
            # generate random x and y
            location = Point(x=random.random(),y=random.random())
            # create a drone object
            drone = Drone(location=location)
            # add to the current list of drones
            self.drones.append(drone)
    
    def run (self,timesteps=30):
        
        intrest_locations = [
            Point(0.4,0.8),
            Point(0.3,0.1),
            Point(0.7,0.2),
            Point(0.9,0.9),
        ]
        for drone in self.drones:
            self.drone.target = random.choice(intrest_locations)

        for i in range(0,timesteps):
            for drone in self.drones:
                drone.moveToPoint(drone.target)


        for drone in self.drones:
            print (drone)

