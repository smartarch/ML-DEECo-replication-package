from enum import IntEnum
from typing import Optional
import tensorflow as tf

from ml_deeco.simulation import Agent, Point
from ml_deeco.estimators import ValueEstimate, NeuralNetworkEstimator


class DroneState(IntEnum):
    AVAILABLE = 0
    LOADED = 1
    MOVING_TO_CHARGER = 2
    AT_CHARGER = 3
    TERMINATED = 4


droneBatteryEstimator = NeuralNetworkEstimator(
    hidden_layers=[],  # No hidden layers -> linear regression
    optimizer=tf.optimizers.Adam(learning_rate=0.1),
    outputFolder="results/drone_battery", name="Drone Battery"
)


class Drone(Agent):

    def __init__(self, location):
        super().__init__(location, speed=1)
        self.battery = 1
        self.state = DroneState.AVAILABLE
        self.target: Optional[Point] = None
        self.charger = self.location
        self.useEstimate = False

    futureBatteryEstimate = ValueEstimate().inTimeSteps(10).using(droneBatteryEstimator)

    @futureBatteryEstimate.input()
    @futureBatteryEstimate.target()
    def battery(self):
        return self.battery

    @futureBatteryEstimate.inputsValid
    @futureBatteryEstimate.targetsValid
    def not_terminated(self):
        return self.state != DroneState.TERMINATED and self.state != DroneState.AT_CHARGER

    def actuate(self):

        if self.state == DroneState.MOVING_TO_CHARGER:
            if self.move(self.charger):
                self.state = DroneState.AT_CHARGER

        elif self.state == DroneState.LOADED:
            if self.move(self.charger):
                self.unload()

        elif self.state == DroneState.AVAILABLE:
            if self.target is not None:
                if self.move(self.target):
                    self.load()
            if self.useEstimate:
                if self.futureBatteryEstimate() < 0:
                    self.state = DroneState.MOVING_TO_CHARGER

        if self.battery <= 0:
            self.battery = 0
            self.state = DroneState.TERMINATED

    def load(self):
        print("Package loaded")
        self.target = None
        self.state = DroneState.LOADED

    def unload(self):
        print("Package unloaded")
        self.state = DroneState.AVAILABLE

    def move(self, target):
        if self.state == DroneState.LOADED:
            self.battery -= 0.02
        else:
            self.battery -= 0.01
        return super().move(target)
