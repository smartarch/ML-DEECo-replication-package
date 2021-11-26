import os
import numpy as np
import abc

from common.serialization import Log

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # disable GPU in TF
import tensorflow as tf


class Estimator:

    def __init__(self, inputs):
        """

        Parameters
        ----------
        inputs : dict[str, Feature]
        """

        self._inputs = inputs
        self._numFeatures = 0
        for feature in self._inputs.values():
            self._numFeatures += feature.getNumFeatures()

        self._model = self.construct_model()
        self._model.summary()

        self._data_x = []
        self._data_y = []

    def construct_model(self):

        hidden_layer = 20

        inputs = tf.keras.layers.Input([self._numFeatures])
        hidden = tf.keras.layers.Dense(hidden_layer, activation=tf.keras.activations.relu)(inputs)
        output = tf.keras.layers.Dense(1, activation=tf.keras.activations.exponential)(hidden)

        model = tf.keras.Model(inputs=[inputs], outputs=[output])
        model.compile(
            tf.optimizers.Adam(),
            tf.losses.Poisson(),
        )

        return model

    def predict(self, observations):
        raise NotImplementedError()

    def train(self):
        x = np.array(self._data_x)
        y = np.array(self._data_y)
        self._model.fit(x, y,
                        epochs=10)  # TODO(MT): epochs

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

    def endIteration(self):
        """Called at the end of the iteration. We want to start the training now."""
        self.train()


class TimeEstimator(Estimator):

    def __init__(self, inputs):
        super().__init__(inputs)
        self._records = {}

    def collectRecordStart(self, recordId, x, timeStep):
        if recordId not in self._records:
            self._records[recordId] = TimeEstimator.TimeEstimatorRecord(x, timeStep)

    def collectRecordEnd(self, recordId, timeStep):
        if recordId not in self._records:
            raise KeyError(f"RecordId {recordId} not found. The record collection must be first started using the 'collectRecordStart' method.")

        record = self._records[recordId]
        del self._records[recordId]

        timeDifference = timeStep - record.startTime
        self.collectRecord(record.x, timeDifference)

    class TimeEstimatorRecord:
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
        # TODO(MT): normalization
        return np.array([value])


# https://www.tensorflow.org/api_docs/python/tf/keras/layers/CategoryEncoding
# https://www.tensorflow.org/api_docs/python/tf/keras/layers/IntegerLookup
# https://www.tensorflow.org/api_docs/python/tf/keras/layers/Concatenate
