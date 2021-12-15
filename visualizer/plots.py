import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import statistics

font = {'size'   : 12}

matplotlib.rc('font', **font)

def createLogPlot(log, filename, title):
    fig, axs = plt.subplots(2,2, figsize=(10,10))
    
    colors = [
        'blue',
        'orange',
        'green'
    ]

    x = np.arange(len(log)-1)
    labels = log[0]
    array = np.array(log[1:])
    width = 0.35
    
    axes = [
        axs[0,0],
        axs[0,1],
        axs[1,0]
    ]

    statisticsArray = np.zeros((3,len(log)-1))

    for i in range(3):
        axes[i].set_xlabel('Runs')
        axes[i].set_ylabel(labels[i])
        axes[i].bar(x,array[:,i],width=width,color=colors[i])

        statisticsArray[i] = np.array(
            array[:,i]/max(array[:,i]))
        axs[1,1].plot(x,statisticsArray[i],color=colors[i],label=labels[i])
        


        axs[1,1].set_xlabel('Runs')
        axs[1,1].set_ylabel("Rate")

    axs[1,1].legend()
    fig.suptitle(title, fontsize=16)
    fig.tight_layout()
    plt.savefig(filename)
    plt.show()


