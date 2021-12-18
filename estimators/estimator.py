"""
General code for estimators
"""

import os
import abc
from datetime import datetime
from matplotlib import pyplot as plt
import numpy as np

from estimators.features import Feature
from utils.serialization import Log

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf


######################
# Baseline estimator #
######################


class BaselineTimeEstimator(Estimator):

    def predict(self, observation):
        return 0

    def createDataCollector(self, inputs):
        return TimeDataCollector(inputs)


class BaselineEstimation(Estimation):

    @property
    def name(self):
        return "Baseline 0"

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

    def preprocess(self, observation):
        return np.concatenate([
            feature.preprocess(observation[featureName])
            for featureName, feature in self._inputs.items()
        ])

    def predict(self, observation):
        record = self.preprocess(observation)

        # noinspection PyUnresolvedReferences
        predictions = self._estimation.model([record]).numpy()[0]
        return predictions[0]

    def predictBatch(self, observations):
        records = np.array([self.preprocess(o) for o in observations])
        # noinspection PyUnresolvedReferences
        predictions = self._estimation.model(records).numpy()
        return predictions[:, 0]


    def createDataCollector(self, inputs):
        return TimeDataCollector(inputs)


class NeuralNetworkTimeEstimation(Estimation):

    @property
    def name(self):
        return f"Neural network {self._hidden_layers}"

    def __init__(self, inputs, hidden_layers, **kwargs):
        super().__init__(inputs, **kwargs)

        self._numFeatures = 0
        for feature in self._inputs.values():
            self._numFeatures += feature.getNumFeatures()

        self._hidden_layers = hidden_layers
        # For the sake of simulation, we use the same model in all the estimators. In practice, each NeuralNetworkTimeEstimator could have its own model and the train method of the NeuralNetworkTimeEstimation could update all the models.
        self.model = self.constructModel(hidden_layers)

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
        epochs = 50
        history = self.model.fit(x, y,
                                 epochs=epochs,
                                 validation_split=0.2,
                                 callbacks=[tf.keras.callbacks.EarlyStopping(patience=10)],
                                 verbose=2 if self._args.verbose > 1 else 0)

        trainLog = Log(["epoch", "train_mse", "val_mse"])
        for row in zip(range(1, epochs + 1), history.history["mean_squared_error"], history.history["val_mean_squared_error"]):
            trainLog.register(row)
        trainLog.export(f"{self._outputFolder}/waiting-time-{self._iteration}-training.csv")

    def _createEstimator(self, inputs):
        return NeuralNetworkTimeEstimator(self, inputs)

    def _evaluate_predict(self, x):
        return self.model(x).numpy()

    def save(self):
        self.model.save(f"{self._outputFolder}/waiting-time-model.h5")
