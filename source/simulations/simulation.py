# import random
import os
from datetime import date

from source.components.agent import Agent
from source.ensembles.charge import PrivateChargerAssignment 
from source.ensembles.protect import FieldProtection
from source.simulations.monitor import Monitor
from source.simulations.serializer import Report
from source.simulations.visualizers import Visualizer
class Simulation:

    def __init__(self, world, visualize = True):
        self.visualize = visualize
        self.world = world

    def setFieldProtectionEnsembles(self):
        fieldProtectionEnsembles= []
        for field in self.world.fields:
            fieldProtectionEnsembles.append (FieldProtection(field))

        fieldProtectionEnsembles = sorted(fieldProtectionEnsembles, key=lambda x: -x.size())
        totalDrones = len(self.world.drones) - len(fieldProtectionEnsembles)
        circularIndex = 0
        for i in range(totalDrones):
            totalDrones = fieldProtectionEnsembles[circularIndex].assignCardinality(1)
            circularIndex = (circularIndex+1) % len(fieldProtectionEnsembles)

        instantiatedEnsembles = []
        for ens in fieldProtectionEnsembles:
            if ens.materialize(self.world.drones, instantiatedEnsembles):
                instantiatedEnsembles.append(ens)

        return instantiatedEnsembles

    def setPrivateChargers(self):
        privateChargers = []
        for drone in self.world.drones:
            privateChargers.append (PrivateChargerAssignment(drone))
        
                
        instantiatedEnsembles = []
        for ens in privateChargers:
            if ens.materialize(self.world.chargers, instantiatedEnsembles):
                instantiatedEnsembles.append(ens)

        return instantiatedEnsembles

    def run (self):
        agents = [agent for agent in self.world.map if isinstance(agent, Agent)]
        agentReporter = Report(Agent)
        worldReporter = Report(Monitor)

        monitor = Monitor()

        if self.visualize:
            visualizer = Visualizer (self.world)
            visualizer.drawFields()
        
        instantiatedEnsembles = self.setFieldProtectionEnsembles()
        instantiatedEnsembles.extend(self.setPrivateChargers())

        for i in range(self.world.maxSteps):
            for agent in agents:
                agent.actuate()
                agent.report(i)

            for ens in instantiatedEnsembles:
                ens.actuate()
            
            monitor.report(i,self.world)
            if self.visualize:
                visualizer.drawComponents(i+1)
        
        folder = "results"
        if not os.path.exists(folder):
            os.makedirs(folder)

        today = date.today().strftime("%Y%m%d")
        
        if self.visualize:
            visualizer.createAnimation(f"{folder}/simulation-{today}.gif")

        agentReporter.export(f"{folder}/agents-{today}.csv")
        worldReporter.export(f"{folder}/world-{today}.csv")

       
  


