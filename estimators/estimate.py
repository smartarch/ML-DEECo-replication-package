"""
Estimates
"""
from enum import Enum, auto
from collections import namedtuple
from types import MethodType
from typing import Callable, List

import numpy as np

from estimators.features import Feature


BoundFeature = namedtuple('BoundFeature', ('name', 'feature', 'function'))


class DataCollectorMode(Enum):
    First = auto()  # keep only the first record for each recordId
    Last = auto()   # keep only the last record for each recordId
    All = auto()    # keep all records for each recordId


class DataCollector:

    def __init__(self, mode=DataCollectorMode.First):
        self._records = {}
        self._mode = mode
        self.x = []
        self.y = []

    def collectRecordInputs(self, recordId, x, force_replace=False):
        if recordId not in self._records or force_replace:
            self._records[recordId] = []

        records = self._records[recordId]
        if self._mode == DataCollectorMode.All:
            records.append(x)
        elif self._mode == DataCollectorMode.First:
            if len(records) == 0:
                records.append(x)
        elif self._mode == DataCollectorMode.Last:
            if len(records) == 0:
                records.append(x)
            else:
                records[0] = x

    def collectRecordTargets(self, recordId, y):
        if recordId not in self._records:
            raise KeyError(f"RecordId {recordId} not found. The record inputs must be collected first using the 'collectRecordInputs' method.")

        records = self._records[recordId]
        del self._records[recordId]

        for x in records:
            self.x.append(x)
            if callable(y):
                self.y.append(y(x))
            else:
                self.y.append(y)


class Estimate:

    def __init__(self, estimation):
        from estimators.estimation import Estimation  # for type annotation
        self.estimation: Estimation = estimation
        estimation.assignEstimate(self)
        self.inputs: List[BoundFeature] = []
        self.targets: List[BoundFeature] = []
        self.idFunction = None
        self.dataCollector = DataCollector()

    def input(self, feature=None):
        """Defines an input feature"""
        if feature is None:
            feature = Feature()

        def addInputFunction(function):
            self._addInput(function.__name__, feature, function)
            return function

        return addInputFunction

    def target(self, feature=None):
        """Defines a target value"""
        if feature is None:
            feature = Feature()

        def addTargetFunction(function):
            self._addTarget(function.__name__, feature, function)
            return function

        return addTargetFunction

    def id(self, function):
        self.idFunction = function
        return function

    def _addInput(self, name: str, feature: Feature, function: Callable):
        self.inputs.append(BoundFeature(name, feature, function))

    def _addTarget(self, name: str, feature: Feature, function: Callable):
        self.targets.append(BoundFeature(name, feature, function))

    def estimate(self, *args):
        record = []
        for name, feature, function in self.inputs:
            value = function(*args)
            value = feature.preprocess(value)
            record.append(value)
        x = np.concatenate(record)

        recordId = self.idFunction(*args)
        self.dataCollector.collectRecordInputs(recordId, x)

        prediction = self.estimation.predict(x)

        if len(prediction) == 1:
            prediction = prediction[0]
        return prediction.tolist()

    def collect(self, *args):
        record = []
        for name, feature, function in self.targets:
            value = function(*args)
            value = feature.preprocess(value)
            record.append(value)
        y = np.concatenate(record)

        recordId = self.idFunction(*args)
        self.dataCollector.collectRecordTargets(recordId, y)

    def getData(self):
        return self.dataCollector.x, self.dataCollector.y


class SelectionTimeEstimate(Estimate):

    def __init__(self, estimation):
        super().__init__(estimation)
        self.targets.append(BoundFeature("time", Feature(), lambda x: 0))  # TODO(MT)


class ListWithSelectionTimeEstimate(list):
    selectionTimeEstimate = None


def addSelectionTimeEstimate(compSelector, estimation):
    compSelector.selectionTimeEstimate = SelectionTimeEstimate(estimation)
    origGet = compSelector.get

    def newGet(self, instance, owner):
        sel = origGet(instance, owner)
        if isinstance(sel, list):
            sel = ListWithSelectionTimeEstimate(sel)
        sel.selectionTimeEstimate = compSelector.selectionTimeEstimate
        return sel

    # TODO(MT): modify execute to collect training data

    compSelector.get = MethodType(newGet, compSelector)
    return compSelector
