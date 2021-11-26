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
        self._model = self.construct_model()
        self._model.summary()

        self._data_x = []
        self._data_y = []

    def construct_model(self):

        numFeatures = 0
        for feature in self._inputs.values():
            numFeatures += feature.getNumFeatures()

        hidden_layer = 20

        inputs = tf.keras.layers.Input([numFeatures])
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

    def train(self, x, y):
        # TODO(MT): use collected records
        self._model.fit(x, y,
                        epochs=10)  # TODO(MT): epochs

    def collectRecord(self, x, y):
        # TODO(MT): preprocess
        print(x, y)
        self._data_x.append(x)
        self._data_y.append(y)

    def dumpData(self, fileName):
        dataLogHeader = []
        for featureName, feature in self._inputs.items():
            dataLogHeader.extend(feature.getHeader(featureName))
        dataLogHeader.append("target")

        dataLog = Log(dataLogHeader)

        for x, y in zip(self._data_x, self._data_y):
            dataLog.register([x, y])  # TODO(MT)

        dataLog.export(fileName)

    def endIteration(self):
        """Called at the end of the iteration. We want to start the training now."""
        # TODO(MT)
        pass


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


class IntEnumFeature(Feature):

    def __init__(self, enumClass):
        self.enumClass = enumClass

    def getNumFeatures(self):
        return len(self.enumClass)

    def getHeader(self, featureName):
        return [f"{featureName}_{item}" for item, _ in self.enumClass.__members__.items()]


class FloatFeature(Feature):

    def __init__(self, min, max):
        self.min = min
        self.max = max


# if __name__ == "__main__":
#     estimator = Estimator()
#
#     x = np.array([
#         [1, 2, -3, -1],
#         [1, 2, 2, -2],
#         [-1, 1, 2, -2],
#     ])
#     y = np.array([
#         [1],
#         [2],
#         [1]
#     ])
#     estimator.train(x, y)


# https://www.tensorflow.org/api_docs/python/tf/keras/layers/CategoryEncoding
# https://www.tensorflow.org/api_docs/python/tf/keras/layers/IntegerLookup
# https://www.tensorflow.org/api_docs/python/tf/keras/layers/Concatenate
