import matplotlib.pyplot as plt
import numpy as np


def plotLines(x,y):
  
    # plot
    fig, ax = plt.subplots()
    for line in y:
        ax.plot(x, line, '-')
    plt.show()

