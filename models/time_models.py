from ..common.components import DroneState,BirdState
from ..common.serialization import Log
import statistics


class TimeModel:
    
    timeLogHeader = [
    'timestep',
    'deadDrones',
    'chargingDrones',
    'meanBattery',
    'minAlert',
    'maxAlert',
    'aliveRate',
    'freeChargers',
    'eatingBirds',
    'damage',
    'energy',
]
    def __init__(self,world,simulation):
        self.world = world
        self.simulation = simulation
        self.log = Log(TimeModel.timeLogHeader)


    def addRecord(self):
        record = [
            self.world.currentTimeStep,
            len([drone for drone in self.world.drones if drone.state==DroneState.TERMINATED])/len(self.world.drones),
            len([drone for drone in self.world.drones if drone.state==DroneState.CHARGING]),
            statistics.mean([drone.battery for drone in self.world.drones if drone.state!=DroneState.TERMINATED ]),
            min([drone.alert for drone in self.world.drones if drone.state!=DroneState.TERMINATED ]),
            max([drone.alert for drone in self.world.drones if drone.state!=DroneState.TERMINATED ]),
            len([drone.alert for drone in self.world.drones if drone.state!=DroneState.TERMINATED ])/len(self.world.drones),
            len([charger for charger in self.world.chargers if not charger.occupied]),
            len([bird for bird in self.world.birds if bird.state==BirdState.EATING]),
            sum([bird.ate for bird in self.world.birds])/self.world.totalPlaces,
            sum([charger.energyConsumed for charger in self.world.chargers]),
        ]

        self.log.register(record)

    def dump (self,filename):
        self.log.export(filename)
