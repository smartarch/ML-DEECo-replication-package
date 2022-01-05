import os
import argparse
from datetime import datetime
import random
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt


mapComparisionChart = {
    'inputs':[
        'results//evaluation//small//small_1_1.csv',
        'results//evaluation//intense//intense_1_1.csv',
        'results//evaluation//medium//medium_1_1.csv',
        'results//evaluation//large//large_1_1.csv',
    ],
    'subtitles':[
        'Small Map',
        'Intense Map',
        'Medium Map',
        'Large Map'
    ],
    'y':[
        'Drone Live Rate',
        'Total Damage Rate',
        'Energy Consumed Rate',
    ],
    'x':'Iterations',
    'colors':[
        'blue',
        'orange',
        'yellowgreen',
    ],
    'type':'bar',
    'folder':'results//evaluation//charts',
    'filename':'map-comparision',
    'extention':'tiff',
    'dpi':300,
    'size':(10,8),
    'title':'Simulation Maps with Different Configurations'
}

chargeAlertChart = {
    'inputs':[
        'results//evaluation//chargeAlert//small//log_baseline_zero.csv',
        'results//evaluation//chargeAlert//intense//log_baseline_zero.csv',
        'results//evaluation//chargeAlert//medium//log_baseline_zero.csv',
        'results//evaluation//chargeAlert//large//log_baseline_zero.csv',
    ],
    'subtitles':[
        'Small Map',
        'Intense Map',
        'Medium Map',
        'Large Map'
    ],
    'y':[
        'Active Drones',
        'Total Damage',
        'Energy Consumed',
    ],
    'x':'Charge Alert',
    'colors':[
        'blue',
        'orange',
        'yellowgreen',
    ],
    'type':'line',
    'folder':'results//evaluation//charts',
    'filename':'charge-alert',
    'extention':'png',
    'dpi':600,
    'size':(10,8),
    'title':'Simulation Runs in Multiple Maps Tuning Charging Alerts'
}


randomBattery = {
    'inputs':[
        'results//evaluation//batteryRandom//small//log_baseline_zero.csv',
        'results//evaluation//batteryRandom//intense//log_baseline_zero.csv',
        'results//evaluation//batteryRandom//medium//log_baseline_zero.csv',
        'results//evaluation//batteryRandom//large//log_baseline_zero.csv',
    ],
    'subtitles':[
        'Small Map',
        'Intense Map',
        'Medium Map',
        'Large Map'
    ],
    'y':[
        'Active Drones',
        'Total Damage',
        'Energy Consumed',
    ],
    'x':'Max Random Battery Decrease',
    'colors':[
        'blue',
        'orange',
        'yellowgreen',
    ],
    'type':'line',
    'folder':'results//evaluation//charts',
    'filename':'random-battery',
    'extention':'png',
    'dpi':600,
    'size':(10,8),
    'title':'Simulation Runs in Multiple Maps Tuning Starting Battery Decrease'
}

droneSurvived = {
    'inputs':[
        'results//evaluation//vision//drones_survived.csv',
    ],
    'subtitles':[
        'Survived Drones',
    ],
    'y':[
        'Small',
        'Intense',
        'Medium',
        'Large',
    ],
    'x':'Iterations',
    'colors':[
        'lightblue',
        'orange',
        'blue',
        'green',
    ],
    'type':'line',
    'folder':'results//evaluation//charts',
    'filename':'survived_drones',
    'extention':'png',
    'dpi':600,
    'size':(8,6),
    'title':'Survived Drones in Different Simulation Maps over 500 Iterations'
}
droneAfterNN = {
    'inputs':[
        'results//evaluation//methods//drones.csv',
    ],
    'subtitles':[
        'Survived Drones Average of 6 Simulation Runs',
    ],
    'y':[
        'No Estimator',
        'Neural Network',
    ],
    'x':'Method',
    'colors':[
        'lightblue',
        'orange',
        'blue',
        'green',
    ],
    'width':0.5,
    'type':'bar',
    'folder':'results//evaluation//charts',
    'filename':'drones_nn',
    'extention':'png',
    'dpi':600,
    'size':(8,6),
    'title':'Survived Drones Comparision of No Estimator vs Neural Network Estimator'
}
energyDamageAfterNN = {
    'inputs':[
        'results//evaluation//methods//damage.csv',
        'results//evaluation//methods//energy.csv',
    ],
    'subtitles':[
        'Avarage Damage in 6 Runs',
        'Avarage Energy Consumed in 6 Runs',
    ],
    'y':[
        'No Estimator',
        'Neural Network',
    ],
    'x':'Map',
    'colors':[
        'lightblue',
        'orange',
        'blue',
        'green',
    ],
    'width':0.5,
    'type':'bar',
    'folder':'results//evaluation//charts',
    'filename':'energy_damage_nn',
    'extention':'png',
    'dpi':600,
    'size':(8,6),
    'title':'Comparision of No Estimator vs Neural Network Estimator'
}
class Chart:
    def __init__ (self, chart):
        
        self.inputs = chart['inputs']
        self.subtitles = chart['subtitles']
        self.subplots = len(self.inputs)
        self.colors = chart['colors']
        self.title = chart['title']
        self.folder = chart['folder']    
        self.filename = f"{self.folder}//{chart['filename']}.{chart['extention']}"
        self.x = chart['x']
        self.y = chart['y']
        subcols = round(math.sqrt(self.subplots))
        subrows = math.ceil(math.sqrt(self.subplots))
        figsize = chart['size']
        dpi = chart['dpi']

        self.fig, matrixAxs = plt.subplots(subrows,subcols, figsize=figsize,dpi=dpi)
        self.axes = []
        try:
            for ax in matrixAxs:
                try:
                    for subAx in ax:
                        self.axes.append(subAx)
                except:
                    self.axes.append(ax)
        except:
            self.axes.append(matrixAxs)

    def plot(self):
        pass

class BarChart(Chart):
    def __init__(self,chart):
        Chart.__init__(self,chart)
        self.width= chart['width'] / len(chart['y'])

    def plot (self):
        for subplot in range(self.subplots):
            dataFrame = pd.read_csv(self.inputs[subplot])
            xLabels = dataFrame[self.x]
            x = np.arange(0,len(xLabels))
            
            for i,y in enumerate(self.y):
                yArray = np.array(dataFrame[y])
                self.axes[subplot].bar(x+(self.width*(i-1)), yArray, color=self.colors[i], label=y, width=self.width)
            
            self.axes[subplot].legend()
            self.axes[subplot].set_ylabel(self.subtitles[subplot])
            self.axes[subplot].set_xlabel(self.x)
            self.axes[subplot].set_xticks(x, labels=xLabels)

        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        self.fig.suptitle(self.title, fontsize=12)
        self.fig.tight_layout()
        plt.savefig(self.filename)
        #plt.show()
        plt.close(self.fig)

 
        
class LineChart(Chart):
    def __init__(self,chart):
        Chart.__init__(self,chart)
    def plot (self):

        for subplot in range(self.subplots):
            dataFrame = pd.read_csv(self.inputs[subplot])
            xLabels = dataFrame[self.x]
            x = np.arange(0,len(xLabels))
            
            for i,y in enumerate(self.y):
                yArray = np.array(dataFrame[y])
                self.axes[subplot].plot(x, yArray, color=self.colors[i], label=y)
            
            self.axes[subplot].legend()
            self.axes[subplot].set_ylabel(self.subtitles[subplot])
            self.axes[subplot].set_xlabel(self.x)
            self.axes[subplot].set_xticks(x, labels=[f"{xLb}" for xLb in xLabels])

        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        self.fig.suptitle(self.title, fontsize=12)
        self.fig.tight_layout()
        plt.savefig(self.filename)
        #plt.show()
        plt.close(self.fig)

 


def main():
    
    charts = [
        # randomBattery,
        # chargeAlertChart,
        # mapComparisionChart,
        droneAfterNN,
        energyDamageAfterNN

    ]

    for chart in charts:
        if chart['type'] == 'bar':
            barChart = BarChart(chart)
            barChart.plot()

        if chart['type'] == 'line':
            lineChart = LineChart(chart)
            lineChart.plot()
    
if __name__ == "__main__":
    main()

