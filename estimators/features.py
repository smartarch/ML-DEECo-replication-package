import numpy as np
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf


class Feature:

    @staticmethod
    def getNumFeatures():
        return 1

    @staticmethod
    def getHeader(featureName):
        return [featureName]

    def preprocess(self, value):
        return np.array([value])

    def postprocess(self, value):
        return value[0]


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

    def postprocess(self, value):
        return self.enumClass(np.argmax(value))


class CategoricalFeature(Feature):

    def __init__(self, categories: list):
        self.categories = categories
        self.numItems = len(self.categories)

    def getNumFeatures(self):
        return self.numItems

    def getHeader(self, featureName):
        return [f"{featureName}_{item}" for item in self.categories]

    def preprocess(self, value):
        index = self.categories.index(value)
        return tf.one_hot(index, self.numItems).numpy()

    def postprocess(self, value):
        return self.categories[np.argmax(value)]


class FloatFeature(Feature):

    def __init__(self, min, max):
        self.min = min
        self.max = max
        self.diff = max - min

    def preprocess(self, value):
        normalized = (value - self.min) / self.diff
        return np.array([normalized])

    def postprocess(self, value):
        return value[0] * self.diff + self.min
