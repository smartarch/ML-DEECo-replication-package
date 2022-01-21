import enum
from typing import Union, List, Type
import numpy as np
import os
# os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # Report only TF errors by default
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU in TF. The models are small, so it is actually faster to use the CPU.
import tensorflow as tf


class Feature:

    @staticmethod
    def getNumFeatures():
        return 1

    @staticmethod
    def getHeader(featureName):
        return [featureName]

    def preprocess(self, value):
        return np.array([value], dtype=np.float32)

    def postprocess(self, value):
        return value[0]


class CategoricalFeature(Feature):

    def __init__(self, categories: Union[List, Type[enum.IntEnum]]):
        """
        Feature for a known set of possible categories. Preprocessing is done by one-hot encoding.

        Parameters
        ----------
        categories
            List of possible values or an IntEnum class.
        """
        assert len(categories) > 0, "CategoricalFeature: The number of categories must be bigger than 0."
        self.categories = categories
        self.numItems = len(self.categories)

    def getNumFeatures(self):
        return self.numItems

    def isEnum(self):
        return isinstance(self.categories, type) and issubclass(self.categories, enum.IntEnum)

    def getHeader(self, featureName):
        if self.isEnum():
            return [f"{featureName}_{item}" for item, _ in self.categories.__members__.items()]
        else:
            return [f"{featureName}_{item}" for item in self.categories]

    def preprocess(self, value):
        if self.isEnum():
            index = int(value)
        else:
            index = self.categories.index(value)
        return tf.one_hot(index, self.numItems).numpy()

    def postprocess(self, value):
        if self.isEnum():
            return self.categories(np.argmax(value))
        else:
            return self.categories[np.argmax(value)]


class BinaryFeature(Feature):

    def postprocess(self, value):
        return super().postprocess(value) > 0.5


class FloatFeature(Feature):

    def __init__(self, min, max):
        # assert min < max, "FloatFeature: The minimum must be strictly smaller than the maximum."  # TODO: this raises exception with 0 drones, otherwise, it seems useful
        self.min = min
        self.max = max
        self.diff = max - min

    def preprocess(self, value):
        normalized = (value - self.min) / self.diff
        return np.array([normalized])

    def postprocess(self, value):
        return value[0] * self.diff + self.min


class TimeFeature(Feature):
    """This is used for automatic activation and loss inference."""
    pass
