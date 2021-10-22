from .base import *
import random

class World:
    drones : list()


    def generate_random_drones(self,max_number = 100 ,radnom_seed=23913):
        # random location
        random.seed(radnom_seed)
        self.drones = list()

        # generate max number drones, and append them to the drones list
        for i in range(0,max_number):
            location = Point(random.random(),random.random())
            drone = Drone(location)
            self.drones.append(drone)

        return self.drones
