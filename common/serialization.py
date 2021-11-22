from common.components import Component, BirdState, DroneState

class Report:
    def write (self,component,timeStep):
        self.context += str(timeStep) + ","
        for key in component.__dict__:
            self.context += f"{component.__dict__[key]},"
        self.context = self.context[:-1]+"\n" 

    def __init__ (self, componentClass):
        self.context = componentClass.header + "\n"
        componentClass.reporter = self.write
  
    def export (self, filename):
        file = open (filename,'w')
        file.write(self.context)
        file.close()

    def __str__ (self):
        return self.context

class Monitor:

    reporter = None
    header=  "timestep,protectingDrones,chargingDrones,deadDrones,allBirds,eatingBirds,allChargers,idleChargers,energyConsumed,damageRate"
                


    def report(self,timeStep,world):
        world = world

        self.protectingDrones = len([drone for drone in world.drones if drone.state==DroneState.PROTECTING or drone.state==DroneState.MOVING_TO_FIELD])
        self.chargingDrones = len([drone for drone in world.drones if drone.state==DroneState.CHARGING])
        self.deadDrones = len([drone for drone in world.drones if drone.state==DroneState.TERMINATED])
        self.allBirds = len(world.birds)
        self.eatingBirds = len([bird for bird in world.birds if bird.state==BirdState.EATING])
        self.allChargers = len(world.chargers) * world.chargerCapacity
        self.idleChargers = sum([world.chargerCapacity- len(charger.acceptedDrones) for charger in world.chargers])
        self.energyConsumed = 0
        for charger in world.chargers:
            self.energyConsumed += len(charger.acceptedDrones)*world.chargingRate

        eatingSummary = sum([bird.ate for bird in world.birds])



        self.damageRate = eatingSummary/ self.allBirds

        Monitor.reporter(self,timeStep)