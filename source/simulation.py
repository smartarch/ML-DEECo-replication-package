from .base import *
import random

class World:
    drones : list()


    def generate_random_drones(self,max_number = 100 ,radnom_seed=23913):
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

        return self.drones
    
    
