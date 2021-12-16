import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import statistics

font = {'size'   : 12}

matplotlib.rc('font', **font)

def createLogPlot(log, filename, title, size):
    fig, axs = plt.subplots(2,2, figsize=(10,10))
    
    colors = [
        'blue',
        'orange',
        'green',
        'black'
    ]

    x = np.arange(1,len(log))
    xtickLabels = (np.arange(0,size[0]*size[1]) % size[0] + 1).tolist()
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
        axes[i].set_xlabel(f"{size[0]} Runs per train")
        axes[i].set_ylabel(labels[i])
        axes[i].bar(x,array[:,i],width=width,color=colors[i])
        axes[i].set_xticks(x,labels=xtickLabels)
        
        for j in range(1,size[1]):
            axes[i].axvline(x = j*size[0]+0.5, color = colors[3])
        statisticsArray[i] = np.array(
            array[:,i]/max(array[:,i]))
        axs[1,1].plot(x,statisticsArray[i],color=colors[i],label=labels[i])
        

    for j in range(1,size[1]):
        axs[1,1].axvline(x = j*size[0]+0.5, color = colors[3])
    axs[1,1].set_xlabel(f"{size[0]} Runs per train")
    axs[1,1].set_ylabel("Rate")
    axs[1,1].set_xticks(x,labels=xtickLabels)
        
    axs[1,1].legend()
    fig.suptitle(title, fontsize=16)
    fig.tight_layout()
    plt.savefig(filename)
    plt.show()
    plt.close(fig)


