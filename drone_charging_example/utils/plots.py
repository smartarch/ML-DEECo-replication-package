import matplotlib
import matplotlib.pyplot as plt
import numpy as np

font = {'size': 12}

matplotlib.rc('font', **font)


def createLogPlot(log, averageLog, filename, title, size):
    colors = [
        'blue',
        'orange',
        'green',
        'red'
    ]
    fig, axs = plt.subplots(2, 2, figsize=(16, 9))
    x = np.arange(1, len(log.records) + 1)
    t = np.arange(1, len(averageLog.records) + 1)
    xtickLabels = (np.arange(0, size[0] * size[1]) % size[0] + 1).tolist()
    labels = log.header
    array = np.array(log.records)
    width = 0.35

    axes = [
        axs[0, 0],
        axs[0, 1],
        axs[1, 0]
    ]

    statisticsArray = np.array(averageLog.records)

    for i in range(2):
        axes[i].set_xlabel(f"{size[0]} Runs per train")
        axes[i].set_ylabel(labels[i])
        axes[i].bar(x, array[:, i], width=width, color=colors[i])
        axes[i].set_xticks(x, labels=xtickLabels)

        for j in range(1, size[1]):
            axes[i].axvline(x=j * size[0] + 0.5, color=colors[3])
        axs[1, 1].plot(t, statisticsArray[:, i + 2], color=colors[i], label=labels[i])

    axs[1, 1].set_xlabel(f"{size[0]} Trains")
    axs[1, 1].set_ylabel("Rate")
    axs[1, 1].set_xticks(t)

    axs[1, 1].legend()
    fig.suptitle(title, fontsize=16)
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
    fig, axs = plt.subplots(len(logs), figsize=(10, 10))
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
    plt.savefig(filename + ".png")
    # plt.show()
    plt.close(fig)
