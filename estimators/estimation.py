"""
Estimation methods
"""
import abc
import sys
from datetime import datetime
from typing import List
import numpy as np
import os

from matplotlib import pyplot as plt

from estimators.estimate import Estimate, BoundFeature

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf

from utils.serialization import Log
from utils.verbose import verbosePrint


class Estimation(abc.ABC):

    def __init__(self, *, outputFolder, args):
        self.x = []
        self.y = []
        self._outputFolder = outputFolder
        self._args = args
        self._iteration = 0

        self._estimates: List[Estimate] = []
        self._initialized = False
        self._inputs: List[BoundFeature] = []
        self._targets: List[BoundFeature] = []

    @property
    @abc.abstractmethod
    def name(self):
        return ""

    def assignEstimate(self, estimate: Estimate):
        self._estimates.append(estimate)

    def init(self, force=False):
        """This must be run AFTER the input and target features are collected by the estimates."""
        if self._initialized and not force:
            verbosePrint(f"Already initialized ({self.name}).", 4)
            return

        verbosePrint(f"Initializing Estimation ({self.name}) with {len(self._estimates)} estimates assigned.", 2)
        if len(self._estimates) == 0:
            print("WARNING: No Estimates assigned, the Estimation is useless.", file=sys.stderr)

        estimate = self._estimates[0]
        self._inputs = estimate.inputs
        self._targets = estimate.targets

        input_names = [i.name for i in self._inputs]
        target_names = [t.name for t in self._targets]

        verbosePrint(f"{self.name}: inputs {input_names}.", 3)
        verbosePrint(f"{self.name}: targets {target_names}.", 3)

        for est in self._estimates:
            assert [i.name for i in est.inputs] == input_names, f"Estimate {est} has inconsistent input features with the assigned estimation"
            assert [t.name for t in est.targets] == target_names, f"Estimate {est} has inconsistent targets with the assigned estimation"

    def collectData(self):
        for estimate in self._estimates:
            x, y = estimate.getData()
            self.x.extend(x)
            self.y.extend(y)

    def dumpData(self, fileName):
        dataLogHeader = []
        for featureName, feature, _ in self._inputs:
            dataLogHeader.extend(feature.getHeader(featureName))
        for featureName, feature, _ in self._targets:
            dataLogHeader.extend(feature.getHeader(featureName))

        dataLog = Log(dataLogHeader)

        for x, y in zip(self.x, self.y):
            dataLog.register(list(x) + list(y))

        dataLog.export(fileName)

    def saveModel(self):
        pass

    @abc.abstractmethod
    def predict(self, x):
        """
        Parameters
        ----------
        x : np.ndarray
            Inputs, shape: [inputs]

        Returns
        -------
        np.ndarray
            Outputs, shape: [targets]
        """
        return

    def predictBatch(self, X):
        """
        Parameters
        ----------
        X : np.ndarray
            Inputs, shape: [batch_size, inputs]

        Returns
        -------
        np.ndarray
            Outputs, shape: [batch_size, targets]
        """
        return np.array([self.predict(x) for x in X])

    def train(self, X, Y):
        """
        Parameters
        ----------
        X : np.ndarray
            Inputs, shape: [batch, features].
        Y : np.ndarray
            Target outputs, shape: [batch, targets].
        """
        pass

    def evaluate(self, X, Y, label):
        """
        Parameters
        ----------
        X : np.ndarray
            Inputs, shape [batch, features].
        Y : np.ndarray
            Target outputs, shape [batch, targets].
        label : str
        """
        predictions = self.predictBatch(X)

        dataLog = Log(["target", "prediction"])

        for t, p in zip(Y, predictions):
            dataLog.register(list(t) + list(p))

        dataLog.export(f"{self._outputFolder}/waiting-time-{self._iteration}-evaluation-{label}.csv")

        mse = np.mean(np.square(Y - predictions))
        verbosePrint(f"{label} MSE: {mse}", 2)

        self._eval_plot(Y, predictions, label)

    def _eval_plot(self, y_true, y_pred, label):  # TODO(MT): multiple targets
        mse = np.mean(np.square(y_true - y_pred))

        lims = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
        # plt.ioff()
        fig = plt.figure(figsize=(10, 10))
        plt.axes(aspect='equal')
        plt.scatter(y_true, y_pred)
        plt.xlabel('True Values')
        plt.ylabel('Predictions')
        plt.title(f"{self.name}\nIteration {self._iteration}\n{label} MSE: {mse:.3f}")
        plt.xlim(lims)
        plt.ylim(lims)
        plt.plot(lims, lims)
        plt.savefig(f"{self._outputFolder}/waiting-time-{self._iteration}-evaluation-{label}.png")
        plt.close(fig)

    def endIteration(self):
        """Called at the end of the iteration. We want to do the training now."""
        self._iteration += 1

        self.collectData()
        count = len(self.x)
        verbosePrint(f"Iteration {self._iteration} collected {count} records.", 1)
        self.dumpData(f"{self._outputFolder}/waiting-time-{self._iteration}.csv")

        if count > 0:
            x = np.array(self.x)
            y = np.array(self.y)

            indices = np.random.permutation(count)
            test_size = int(self._args.test_split * count)
            train_x = x[indices[:-test_size], :]
            train_y = y[indices[:-test_size], :]
            test_x = x[indices[-test_size:], :]
            test_y = y[indices[-test_size:], :]

            verbosePrint(f"Training {self._iteration} started at {datetime.now()}: ", 1)
            verbosePrint(f"Train data shape: {train_x.shape}, test data shape: {test_x.shape}.", 2)

            self.train(train_x, train_y)
            # self.evaluate(train_x, train_y, label="Train")
            # self.evaluate(test_x, test_y, label="Test")

        # clear the data
        self.x = []
        self.y = []


class BaselineEstimation(Estimation):

    @property
    def name(self):
        return "Baseline 0"

    def predict(self, x):
        num_targets = len(self._targets)
        return np.zeros([num_targets])
