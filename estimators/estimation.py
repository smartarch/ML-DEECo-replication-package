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

    def __init__(self, *, outputFolder, args, name=""):
        self.x = []
        self.y = []
        self._outputFolder = outputFolder
        self._args = args
        self.name = name
        self._iteration = 0

        self._estimates: List[Estimate] = []
        self._initialized = False
        self._inputs: List[BoundFeature] = []
        self._targets: List[BoundFeature] = []

    @property
    @abc.abstractmethod
    def estimationName(self):
        return ""

    def assignEstimate(self, estimate: Estimate):
        self._estimates.append(estimate)

    def init(self, force=False):
        """This must be run AFTER the input and target features are collected by the estimates."""
        if self._initialized and not force:
            verbosePrint(f"Already initialized {self.name} ({self.estimationName}).", 4)
            return

        verbosePrint(f"Initializing Estimation {self.name} ({self.estimationName}) with {len(self._estimates)} estimates assigned.", 2)
        if len(self._estimates) == 0:
            print("WARNING: No Estimates assigned, the Estimation is useless.", file=sys.stderr)

        estimate = self._estimates[0]
        self._inputs = estimate.inputs
        self._targets = estimate.targets

        input_names = [i.name for i in self._inputs]
        target_names = [t.name for t in self._targets]

        verbosePrint(f"{self.estimationName}: inputs {input_names}.", 3)
        verbosePrint(f"{self.estimationName}: targets {target_names}.", 3)

        for est in self._estimates:
            assert [i.name for i in est.inputs] == input_names, f"Estimate {est} has inconsistent input features with the assigned estimation {self.name} ({self.estimationName})"
            assert [t.name for t in est.targets] == target_names, f"Estimate {est} has inconsistent targets with the assigned estimation {self.name} ({self.estimationName})"

        self._initialized = True

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

        dataLog.export(f"{self._outputFolder}/waiting-time-{self._iteration}-evaluation-{label}.csv")  # TODO(MT): file names

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
        plt.title(f"{self.name} ({self.estimationName})\nIteration {self._iteration}\n{label} MSE: {mse:.3f}")
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
        verbosePrint(f"{self.name} ({self.estimationName}): iteration {self._iteration} collected {count} records.", 1)
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

            verbosePrint(f"{self.name} ({self.estimationName}): Training {self._iteration} started at {datetime.now()}: ", 1)
            verbosePrint(f"{self.name} ({self.estimationName}): Train data shape: {train_x.shape}, test data shape: {test_x.shape}.", 2)

            self.train(train_x, train_y)
            self.evaluate(train_x, train_y, label="Train")
            self.evaluate(test_x, test_y, label="Test")

        # clear the data
        self.x = []
        self.y = []


class ZeroEstimation(Estimation):
    """
    Predicts 0 for each target.
    """

    @property
    def estimationName(self):
        return "ZeroEstimation"

    def predict(self, x):
        num_targets = len(self._targets)
        return np.zeros([num_targets])


class NeuralNetworkEstimation(Estimation):

    @property
    def estimationName(self):
        return f"Neural network {self._hidden_layers}"

    def __init__(self, hidden_layers, **kwargs):
        super().__init__(**kwargs)
        self._hidden_layers = hidden_layers
        self._model: tf.keras.Model = None

    def init(self, **kwargs):
        super().init(**kwargs)
        self._model = self.constructModel()

    def constructModel(self) -> tf.keras.Model:
        numFeatures = 0
        for _, feature, _ in self._inputs:
            numFeatures += feature.getNumFeatures()

        inputs = tf.keras.layers.Input([numFeatures])
        hidden = inputs
        for layer_size in self._hidden_layers:
            hidden = tf.keras.layers.Dense(layer_size, activation=tf.keras.activations.relu)(hidden)
        output = tf.keras.layers.Dense(1, activation=tf.keras.activations.exponential)(hidden)

        model = tf.keras.Model(inputs=inputs, outputs=output)
        model.compile(
            tf.optimizers.Adam(),
            tf.losses.Poisson(),
            metrics=[tf.metrics.mse],
        )

        return model

    def predict(self, x):
        return self._model(x.reshape(1, -1)).numpy()[0]

    def predictBatch(self, X):
        return self._model(X).numpy()

    def train(self, x, y):
        epochs = 50
        history = self._model.fit(x, y,
                                  epochs=epochs,
                                  validation_split=0.2,
                                  callbacks=[tf.keras.callbacks.EarlyStopping(patience=10)],
                                  verbose=2 if self._args.verbose > 1 else 0)

        trainLog = Log(["epoch", "train_mse", "val_mse"])
        for row in zip(range(1, epochs + 1), history.history["mean_squared_error"], history.history["val_mean_squared_error"]):
            trainLog.register(row)
        trainLog.export(f"{self._outputFolder}/waiting-time-{self._iteration}-training.csv")  # TODO(MT): file names

    def saveModel(self):
        self._model.save(f"{self._outputFolder}/waiting-time-model.h5")  # TODO(MT): file names
