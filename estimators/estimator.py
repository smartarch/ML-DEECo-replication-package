"""
Estimator methods
"""
import abc
import os
import sys
from datetime import datetime
from typing import List
import numpy as np
from matplotlib import pyplot as plt
import tensorflow as tf

from estimators.estimate import Estimate, BoundFeature
from utils.serialization import Log
from utils.verbose import verbosePrint
from simulation.world import WORLD


#########################
# Estimator base class #
#########################


class Estimator(abc.ABC):

    def __init__(self, *, outputFolder, args, name=""):
        WORLD.estimators.append(self)

        self.x = []
        self.y = []
        os.makedirs(outputFolder, exist_ok=True)
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
    def estimatorName(self):
        return ""

    def assignEstimate(self, estimate: Estimate):
        self._estimates.append(estimate)

    def init(self, force=False):
        """This must be run AFTER the input and target features are collected by the estimates."""
        if self._initialized and not force:
            verbosePrint(f"Already initialized {self.name} ({self.estimatorName}).", 4)
            return

        verbosePrint(f"Initializing Estimator {self.name} ({self.estimatorName}) with {len(self._estimates)} estimates assigned.", 2)
        if len(self._estimates) == 0:
            print("WARNING: No Estimates assigned, the Estimator is useless.", file=sys.stderr)
            raise RuntimeError()  # for debugging, later it can be changed to 'return'

        estimate = self._estimates[0]
        self._inputs = estimate.inputs
        self._targets = estimate.targets

        input_names = [i.name for i in self._inputs]
        target_names = [t.name for t in self._targets]

        verbosePrint(f"{self.estimatorName}: inputs {input_names}.", 2)
        verbosePrint(f"{self.estimatorName}: targets {target_names}.", 2)

        for est in self._estimates:
            assert [i.name for i in est.inputs] == input_names, f"Estimate {est} has inconsistent input features with the assigned estimator {self.name} ({self.estimatorName})"
            assert [t.name for t in est.targets] == target_names, f"Estimate {est} has inconsistent targets with the assigned estimator {self.name} ({self.estimatorName})"
            est.check()

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

        currentIndex = 0
        for targetName, feature, _ in self._targets:
            width = feature.getNumFeatures()
            y_pred = predictions[:, currentIndex:currentIndex + width]
            y_true = Y[:, currentIndex:currentIndex + width]
            currentIndex += width

            if width > 1:
                dataLog = Log([f"target_{i}" for i in range(width)] + [f"prediction_{i}" for i in range(width)])
            else:
                dataLog = Log(["target", "prediction"])

            for t, p in zip(y_true, y_pred):
                dataLog.register(list(t) + list(p))

            dataLog.export(f"{self._outputFolder}/{self._iteration}-evaluation-{label}-{targetName}.csv")

            # TODO(MT): accuracy and confusion matrix for classification tasks
            mse = np.mean(np.square(y_true - y_pred))
            verbosePrint(f"{label} – {targetName} MSE: {mse}", 2)

            self._eval_plot(y_true, y_pred, label, targetName)

    def _eval_plot(self, y_true, y_pred, label, targetName):
        mse = np.mean(np.square(y_true - y_pred))

        lims = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
        # plt.ioff()
        fig = plt.figure(figsize=(10, 10))
        plt.axes(aspect='equal')
        plt.scatter(y_true, y_pred)
        plt.xlabel('True Values')
        plt.ylabel('Predictions')
        plt.title(f"{self.name} ({self.estimatorName})\nIteration {self._iteration}, target: {targetName}\n{label} MSE: {mse:.3f}")
        plt.xlim(lims)
        plt.ylim(lims)
        plt.plot(lims, lims)
        plt.savefig(f"{self._outputFolder}/{self._iteration}-evaluation-{label}-{targetName}.png")
        plt.close(fig)

    def endIteration(self):
        """Called at the end of the iteration. We want to do the training now."""
        self._iteration += 1

        self.collectData()
        count = len(self.x)
        verbosePrint(f"{self.name} ({self.estimatorName}): iteration {self._iteration} collected {count} records.", 1)
        self.dumpData(f"{self._outputFolder}/{self._iteration}-data.csv")

        if count > 0:
            x = np.array(self.x)
            y = np.array(self.y)

            indices = np.random.permutation(count)
            test_size = int(self._args.test_split * count)
            train_x = x[indices[:-test_size], :]
            train_y = y[indices[:-test_size], :]
            test_x = x[indices[-test_size:], :]
            test_y = y[indices[-test_size:], :]

            verbosePrint(f"{self.name} ({self.estimatorName}): Training {self._iteration} started at {datetime.now()}: ", 1)
            verbosePrint(f"{self.name} ({self.estimatorName}): Train data shape: {train_x.shape}, test data shape: {test_x.shape}.", 2)

            self.train(train_x, train_y)
            self.evaluate(train_x, train_y, label="Train")
            self.evaluate(test_x, test_y, label="Test")

        # clear the data
        self.x = []
        self.y = []


#################################
# Constant estimator (baseline) #
#################################


class ConstantEstimator(Estimator):
    """
    Predicts 0 for each target.
    """

    def __init__(self, value=0., *, outputFolder, args, name):
        super().__init__(outputFolder=outputFolder, args=args, name=name)
        self._value = value

    @property
    def estimatorName(self):
        return f"ConstantEstimator({self._value})"

    def predict(self, x):
        numTargets = sum((feature.getNumFeatures() for _, feature, _ in self._targets))
        return np.full([numTargets], self._value)


###################
# Neural networks #
###################


DEFAULT_FIT_PARAMS = {
    "epochs": 50,
    "validation_split": 0.2,
    "callbacks": [tf.keras.callbacks.EarlyStopping(patience=10)],
}


class NeuralNetworkEstimator(Estimator):

    @property
    def estimatorName(self):
        return f"Neural network {self._hidden_layers}"

    def __init__(self, hidden_layers, activation=None, loss=tf.losses.mse, fit_params=None, **kwargs):
        """
        Parameters
        ----------
        hidden_layers: list[int]
            Neuron counts for hidden layers.
        activation
            Activation function for the last layer. Default is no activation (identity).
        loss: tf.keras.losses.Loss
        fit_params: dict
        """
        super().__init__(**kwargs)
        self._hidden_layers = hidden_layers
        self._activation = activation
        self._loss = loss
        self._fit_params = DEFAULT_FIT_PARAMS.copy()
        if fit_params:
            self._fit_params.update(fit_params)
        self._model: tf.keras.Model = None

    def init(self, **kwargs):
        super().init(**kwargs)
        self._model = self.constructModel()

    def constructModel(self) -> tf.keras.Model:
        numFeatures = sum((feature.getNumFeatures() for _, feature, _ in self._inputs))
        numTargets = sum((feature.getNumFeatures() for _, feature, _ in self._targets))

        inputs = tf.keras.layers.Input([numFeatures])
        hidden = inputs
        for layer_size in self._hidden_layers:
            hidden = tf.keras.layers.Dense(layer_size, activation=tf.keras.activations.relu)(hidden)
        output = tf.keras.layers.Dense(numTargets, activation=self._activation)(hidden)

        model = tf.keras.Model(inputs=inputs, outputs=output)
        model.compile(
            tf.optimizers.Adam(),
            self._loss,
            metrics=[tf.metrics.mse],
        )

        return model

    def predict(self, x):
        return self._model(x.reshape(1, -1)).numpy()[0]

    def predictBatch(self, X):
        return self._model(X).numpy()

    def train(self, x, y):
        history = self._model.fit(
            x, y,
            **self._fit_params,
            verbose=2 if self._args.verbose > 1 else 0
        )

        trainLog = Log(["epoch", "train_mse", "val_mse"])
        epochs = range(1, self._fit_params["epochs"] + 1)
        for row in zip(epochs, history.history["mean_squared_error"], history.history["val_mean_squared_error"]):
            trainLog.register(row)
        trainLog.export(f"{self._outputFolder}/{self._iteration}-training.csv")

    def saveModel(self):
        self._model.save(f"{self._outputFolder}/model.h5")
