import numpy as np
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
