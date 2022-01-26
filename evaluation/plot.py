from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import os
import argparse
from datetime import datetime
import random
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import glob


class Chart:
    def __init__ (self, chart):
        
        self.inputs = chart['inputs']
        self.subtitles = chart['subtitles']
        self.subplots = len(self.inputs)
        self.colors = chart['colors']
        self.title = chart['title']
        self.folder = chart['folder']    
        self.filename = f"{self.folder}//{chart['filename']}.{chart['extension']}"
        self.x = chart['x']
        self.y = chart['y']
        self.foreColors = chart['foreColors'] 
        subcols = chart['subcols']
        subrows = chart['subrows']
        figsize = (chart['size'][0],chart['size'][1])
        dpi = chart['dpi']
        if 'lineStyles' in chart:
            self.lineStyles = chart['lineStyles']

        self.legend = True
        if 'legend' in chart:
           self.legend = chart['legend']

        self.width = 0.8
        if 'width' in chart:
           self.width = chart['width']

        if 'yLen' in chart:
           self.yLen = chart['yLen']
        else:
            self.yLen = len(self.y)

        self.yLabel = chart['yLabel']
        self.xLabel = chart['xLabel']
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

    def plot (self):
        barWidth = self.width / self.yLen
        for subplot in range(self.subplots):
            dataFrame = pd.read_csv(self.inputs[subplot])
            xLabels = dataFrame[self.x]
            x = np.arange(0,len(xLabels))
            maxArray = 0
            start = -(self.width/2)-barWidth/2
            for i,y in enumerate(self.y):
                yArray = np.array(dataFrame[y])
                if i%(len(self.y)/self.yLen)==0:
                    start = start + barWidth 
                rect = self.axes[subplot].bar(x+start, yArray, color=self.colors[i], label=y,width=barWidth)
                self.axes[subplot].bar_label(rect, fmt="%.2f",color=self.foreColors[i], fontsize=14)
                if maxArray < max(yArray):
                    maxArray = max(yArray)
                self.axes[subplot].set_ylim(0,maxArray*1.2)
            if self.legend[subplot]:
                self.axes[subplot].legend()
            self.axes[subplot].set_ylabel(self.yLabel)
            self.axes[subplot].set_title(self.subtitles[subplot])
            self.axes[subplot].set_xlabel(self.xLabel)
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
                self.axes[subplot].plot(x, yArray,linestyle=self.lineStyles[i], label=y,cmap = 'RdPu')
            
            if self.legend[subplot]:
                self.axes[subplot].legend()
            self.axes[subplot].set_ylabel(self.yLabel)
            self.axes[subplot].set_title(self.subtitles[subplot])
            self.axes[subplot].set_xlabel(self.xLabel)
            self.axes[subplot].set_xticks(x, labels=[f"{xLb}" for xLb in xLabels])

        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        self.fig.suptitle(self.title, fontsize=12)
        self.fig.tight_layout()
        plt.savefig(self.filename)
        #plt.show()
        plt.close(self.fig)

class LineRateChart(Chart):
    def __init__(self,chart):
        Chart.__init__(self,chart)
    def plot (self):

        for subplot in range(self.subplots):
            dataFrame = pd.read_csv(self.inputs[subplot])
            xLabels = dataFrame[self.x]
            x = np.arange(0,len(xLabels))
            
            for i,y in enumerate(self.y):
                yArray = np.array(dataFrame[y])
                self.axes[subplot].plot(x, yArray/max(yArray), label=y)
            
            self.axes[subplot].legend()
            self.axes[subplot].set_ylabel(self.subtitles[subplot])
            self.axes[subplot].set_xlabel(self.x)
            self.axes[subplot].set_xticks(x, labels=[f"{xLb:0.1f}" for xLb in xLabels])

        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        self.fig.suptitle(self.title, fontsize=12)
        self.fig.tight_layout()
        plt.savefig(self.filename)
        #plt.show()
        plt.close(self.fig)



def run(args):
    charts = []
    globs = args.sources
    files = []
    for g in globs:
        files.extend(glob.glob(g))

    for f in files:
        yamlFile = open(f, 'r')
        yamlObject = load(yamlFile, Loader=Loader)
        yamlObject['extension'] = args.extension
        yamlObject['folder'] = args.output
        yamlObject['dpi'] = args.dpi
        charts.append(yamlObject)

    for chart in charts:
        if chart['type'] == 'bar':
            barChart = BarChart(chart)
            barChart.plot()

        if chart['type'] == 'line':
            lineChart = LineChart(chart)
            lineChart.plot()

        if chart['type'] == 'line-rate':
            lineRateChart = LineRateChart(chart)
            lineRateChart.plot()



def main():
    parser = argparse.ArgumentParser(description='Process YAML source file (S) and create charts.')
    parser.add_argument('sources', metavar='sources',nargs='+', type=str, help='YAML addresses to process.')
    parser.add_argument('-x', '--extension', type=str, help='the extension of the output chart figures.', required=False, default="png")
    parser.add_argument('-o', '--output', type=str, help='the output folder', required=False, default="charts")
    parser.add_argument('-d', '--dpi', type=int, help='DPI of output chart figures.', required=False, default="300")
    args = parser.parse_args()
    run(args)

if __name__ == "__main__":
    main()

