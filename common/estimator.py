"""
General code for estimators
"""

import os
import numpy as np
import abc
from common.serialization import Log
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # disable GPU in TF
import tensorflow as tf


########################
# Abstract definitions #
########################


class Estimation(abc.ABC):

    def __init__(self, inputs, outputFolder):
        """
        Estimation class for managing the estimators to generate the estimates.

        Parameters
        ----------
        inputs : dict[str, Feature]
            Features used for the estimation.
        outputFolder : str
            Name of the folder to save the logs.
        """

        self._inputs = inputs
        self._outputFolder = outputFolder
        self._estimators = []

    def createEstimator(self):
        """

        Returns
        -------
        Estimator
        """
        estimator = self._createEstimator(self._inputs)
        self._estimators.append(estimator)
        return estimator

    @abc.abstractmethod
    def _createEstimator(self, inputs):
        """

        Parameters
        ----------
        inputs : dict[str, Feature]

        Returns
        -------
        Estimator
        """
        return

    def collectData(self, clear=True):
        all_x, all_y = [], []
        for estimator in self._estimators:
            x, y = estimator.dataCollector.getData(clear)
            all_x.extend(x)
            all_y.extend(y)
        return all_x, all_y

    def dumpData(self, fileName, all_x, all_y):
        dataLogHeader = []
        for featureName, feature in self._inputs.items():
            dataLogHeader.extend(feature.getHeader(featureName))
        dataLogHeader.append("target")

        dataLog = Log(dataLogHeader)

        for x, y in zip(all_x, all_y):
            dataLog.register(list(x) + list(y))

        dataLog.export(fileName)

    def save(self):
        pass

    def train(self, x, y):
        """

        Parameters
        ----------
        x : np.ndarray
            Inputs.
        y : np.ndarray
            Target outputs.

        Returns
        -------

        """
        pass

    def evaluate(self, x, y, iteration):
        """

        Parameters
        ----------
        x : np.ndarray
            Inputs, shape [batch, features].
        y : np.ndarray
            Target outputs, shape [batch, 1].
        iteration : int
        """
        predictions = self._evaluate_predict(x)

        dataLog = Log(["target", "prediction"])

        for t, p in zip(y, predictions):
            dataLog.register(list(t) + list(p))

        dataLog.export(f"{self._outputFolder}/waiting-time-{iteration}-evaluation.csv")

    @abc.abstractmethod
    def _evaluate_predict(self, x):
        """
        Generate predictions for evaluation.

        Parameters
        ----------
        x : np.ndarray
            Inputs, shape is [batch, features]

        Returns
        -------
        np.ndarray
            Predictions with shape [batch, 1].
        """
        return np.zeros((x.shape[0], 1))

    def endIteration(self, iteration):
        """Called at the end of the iteration. We want to do the training now."""
        x, y = self.collectData()
        self.dumpData(f"{self._outputFolder}/waiting-time-{iteration}.csv", x, y)

        # TODO: set verbosity level
        print(f"Starting training {iteration + 1} with {len(x)} records")

        x = np.array(x)
        y = np.array(y)

        self.train(x, y)
        self.evaluate(x, y, iteration)

        self._estimators = []


class Estimator(abc.ABC):

    def __init__(self, estimation, inputs):
        """

        Parameters
        ----------
        estimation : Estimation
        inputs : dict[str, Feature]
        """
        self._estimation = estimation
        self.dataCollector = self.createDataCollector(inputs)

    @abc.abstractmethod
    def createDataCollector(self, inputs):
        """

        Parameters
        ----------
        inputs : dict[str, Feature]

        Returns
        -------
        DataCollector
        """
        return

    @abc.abstractmethod
    def predict(self, observation):
        return


######################
# Baseline estimator #
######################


class BaselineTimeEstimator(Estimator):

    def predict(self, observation):
        return 0

    def createDataCollector(self, inputs):
        return TimeDataCollector(inputs)


class BaselineEstimation(Estimation):

    def _createEstimator(self, inputs):
        return BaselineTimeEstimator(self, inputs)

    def _evaluate_predict(self, x):
        return np.zeros((x.shape[0], 1))


################
# NN estimator #
################


class NeuralNetworkTimeEstimator(Estimator):

    def __init__(self, estimation, inputs):
        super().__init__(estimation, inputs)
        self._inputs = inputs

    def predict(self, observation):
        record = np.concatenate([
            feature.preprocess(observation[featureName])
            for featureName, feature in self._inputs.items()
        ]).reshape((1, -1))

        # noinspection PyUnresolvedReferences
        predictions = self._estimation.model(record).numpy()[0]
        return predictions[0]

    def createDataCollector(self, inputs):
        return TimeDataCollector(inputs)


class NeuralNetworkTimeEstimation(Estimation):

    def __init__(self, inputs, outputFolder, hidden_layers):
        super().__init__(inputs, outputFolder)

        self._numFeatures = 0
        for feature in self._inputs.values():
            self._numFeatures += feature.getNumFeatures()

        self.model = self.constructModel(hidden_layers)  # For the sake of simulation, we use the same model in all the estimators. In practice, each NeuralNetworkTimeEstimator could have its own model and the train method of the NeuralNetworkTimeEstimation could update all the models.

    def constructModel(self, hidden_layers):
        """

        Parameters
        ----------
        hidden_layers : list[int]

        Returns
        -------
        tf.keras.Model
        """

        inputs = tf.keras.layers.Input([self._numFeatures])
        hidden = inputs
        for layer_size in hidden_layers:
            hidden = tf.keras.layers.Dense(layer_size, activation=tf.keras.activations.relu)(hidden)
        output = tf.keras.layers.Dense(1, activation=tf.keras.activations.exponential)(hidden)

        model = tf.keras.Model(inputs=[inputs], outputs=[output])
        model.compile(
            tf.optimizers.Adam(),
            tf.losses.Poisson(),
            metrics=[tf.metrics.mse],
        )

        return model

    def train(self, x, y):
        self.model.fit(x, y,
                       epochs=30,
                       validation_split=0.2,
                       callbacks=[tf.keras.callbacks.EarlyStopping(patience=3)],
                       verbose=2)

    def _createEstimator(self, inputs):
        return NeuralNetworkTimeEstimator(self, inputs)

    def _evaluate_predict(self, x):
        return self.model(x).numpy()

    def save(self):
        self.model.save(f"{self._outputFolder}/waiting-time-model.h5")


###################
# Data collection #
###################


class DataCollector:

    def __init__(self, inputs):
        """

        Parameters
        ----------
        inputs : dict[str, Feature]
        """

        self._inputs = inputs

        self._data_x = []
        self._data_y = []

    def collectRecord(self, x, y):
        record = np.concatenate([
            feature.preprocess(x[featureName])
            for featureName, feature in self._inputs.items()
        ])

        self._data_x.append(record)
        self._data_y.append(np.array([y]))

    def dumpData(self, fileName):
        dataLogHeader = []
        for featureName, feature in self._inputs.items():
            dataLogHeader.extend(feature.getHeader(featureName))
        dataLogHeader.append("target")

        dataLog = Log(dataLogHeader)

        for x, y in zip(self._data_x, self._data_y):
            dataLog.register(list(x) + list(y))

        dataLog.export(fileName)

    def getData(self, clear=True):
        x, y = self._data_x, self._data_y
        if clear:
            self._data_x, self._data_y = [], []
        return x, y


class TimeDataCollector(DataCollector):

    def __init__(self, inputs):
        super().__init__(inputs)
        self._records = {}

    def collectRecordStart(self, recordId, x, timeStep, force_replace=False):
        if recordId not in self._records or force_replace:
            self._records[recordId] = TimeDataCollector.TimeRecord(x, timeStep)

    def collectRecordEnd(self, recordId, timeStep):
        if recordId not in self._records:
            raise KeyError(f"RecordId {recordId} not found. The record collection must be first started using the 'collectRecordStart' method.")

        record = self._records[recordId]
        del self._records[recordId]

        timeDifference = timeStep - record.startTime
        self.collectRecord(record.x, timeDifference)

    class TimeRecord:
        def __init__(self, x, startTime):
            self.x = x
            self.startTime = startTime


class Feature(abc.ABC):

    @staticmethod
    def getNumFeatures():
        return 1

    @staticmethod
    def getHeader(featureName):
        return [featureName]

    @abc.abstractmethod
    def preprocess(self, value):
        return np.empty([])


class IntEnumFeature(Feature):

    def __init__(self, enumClass):
        self.enumClass = enumClass
        self.numItems = len(self.enumClass)

    def getNumFeatures(self):
        return self.numItems

    def getHeader(self, featureName):
        return [f"{featureName}_{item}" for item, _ in self.enumClass.__members__.items()]

    def preprocess(self, value):
        return tf.one_hot(int(value), self.numItems).numpy()


class FloatFeature(Feature):

    def __init__(self, min, max):
        self.min = min
        self.max = max

    def preprocess(self, value):
        normalized = (value - self.min) / (self.max - self.min)
        return np.array([normalized])


# https://www.tensorflow.org/api_docs/python/tf/keras/layers/CategoryEncoding
# https://www.tensorflow.org/api_docs/python/tf/keras/layers/IntegerLookup
# https://www.tensorflow.org/api_docs/python/tf/keras/layers/Concatenate
