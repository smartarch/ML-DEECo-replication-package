import matplotlib
import matplotlib.pyplot as plt
import numpy as np

font = {'size': 12}

matplotlib.rc('font', **font)


def createLogPlot(log, averageLog, filename, title, size):
    subtitles = [
        'Survived Drones',
        'Damage Rate'
    ]
    colors = [
        'orange',
        'blue',
    ]
    allX =  np.arange(1, (size[0]*size[1])+1)
    allXLabels =[record[-1] for record in log.records] 

    avXLabels = ['Baseline']
    for av in allX[1:]:
        if (av-1)%size[0] == 0:
            avXLabels.append(f'Train {round((av-1)/5)}')
        else:
            avXLabels.append('')
    mainY =[]
    mainY.append([record[0] for record in log.records])
    mainY.append([record[3] for record in log.records])
    
    averageY = []
    averageSurvived = []
    averageDamage = []
    for record in averageLog.records:
        for t in range(size[0]):
            averageSurvived.append(record[0])
            averageDamage.append(record[3])
    averageY.append(averageSurvived)
    averageY.append(averageDamage)


    fig, axs = plt.subplots(2, 1, figsize=(size[1]+4, size[1]+4))

    for i in range(2):
        twin = axs[i].twiny() 
        if size[1]>1:
            yLines = np.linspace(size[0]+0.5,((size[1]-1)*size[0])+0.5,size[1]-1)
            axs[i].plot(allX, mainY[i], color=colors[0], label="ML Based" , linestyle="solid")
            twin.plot(allX, averageY[i], color=colors[0], label="ML Based - Average" , linestyle="dashed")
            axs[i].vlines(x=yLines, colors='black', ymin=0, ymax=max(averageY[i]), linestyle='dotted')

        axs[i].plot(allX[:size[0]+1], mainY[i][:size[0]+1], color=colors[1], label="Baseline", linestyle="solid")
        twin.plot(allX[:size[0]+1], averageY[i][:size[0]+1], color=colors[1], label="Baseline - Average", linestyle="dashed")

        axs[i].set_xticks(allX, labels=allXLabels)
        axs[i].set_xlabel("Runs")
        twin.set_xticks(allX, labels=avXLabels)
        twin.set_xlabel("Trains")

        axs[i].set_ylabel(subtitles[i])
        axs[i].legend(loc='lower right')
        twin.legend(loc='lower left')
    
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    plt.savefig(filename)
    plt.show()
    plt.close(fig)
    



def createChargerPlot(logs, filename, title):
    colors = [
        'green',
        'yellowgreen',
        'lightcoral',
        'lightblue',
    ]
    fig, axs = plt.subplots(len(logs), figsize=(10, 12))
    if len(logs) == 1:
        axs = [axs]
    x = np.arange(1, len(logs[0].records) + 1)
    labels = logs[0].header
    for i in range(len(logs)):
        array = np.array(logs[i].records)
        axs[i].bar(x, array[:, 0], color=colors[0], label=labels[0], width=1)
        bottom = array[:, 0]
        for j in range(1, array.shape[1]):
            axs[i].bar(x, array[:, j], color=colors[j], label=labels[j], bottom=bottom, width=1)
            bottom = bottom + array[:, j]
        # axs[i].stackplot(x, array.T, labels=labels, colors=colors)  # alternative
        axs[i].legend()
        axs[i].set_title(f"Charger {i + 1}")
        axs[i].set_xlabel("Time Steps")
        axs[i].set_ylabel("Drones")
    fig.suptitle(title, fontsize=16)
    fig.tight_layout()
    plt.savefig(filename + ".png",dpi=600)
    # plt.show()
    plt.close(fig)
