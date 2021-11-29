import pandas as pd
import numpy as np
import plot

datafile = "results/timeLog-medium.csv"
data = pd.read_csv(datafile)
x = np.array(data['timestep'])
#a = np.array(data['damage'])
b = np.array(data['energy'])
#c = np.array(data['aliveRate'])

plot.plotLines(x,[b])
