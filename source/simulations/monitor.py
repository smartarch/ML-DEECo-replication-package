from source.components.drone import DroneState
from source.components.bird import BirdState
class Monitor:

    reporter = None
    header=  "timestep,allDrones,chargingDrones,deadDrones,allBirds,eatingBirds,allChargers,idleChargers,energyConsumed,damageRate"
                


    def report(self,timeStep,world):
        world = world

        self.allDrones = len(world.drones)
        self.chargingDrones = len([drone for drone in world.drones if drone.state==DroneState.CHARGING])
        self.deadDrones = len([drone for drone in world.drones if drone.state==DroneState.TERMINATED])
        self.allBirds = len(world.birds)
        self.eatingBirds = len([bird for bird in world.birds if bird.state==BirdState.EATING])
        self.allChargers = len(world.chargers)
        self.idleChargers = len([charger for charger in world.chargers if charger.client is None])
        self.energyConsumed = 0
        for charger in world.chargers:
            if charger.client is not None:
                self.energyConsumed += charger.rate

        allPlace = 1
        for field in world.fields:
            allPlace += len(field.zones)

        self.damageRate = self.eatingBirds / allPlace

        Monitor.reporter(self,timeStep)
