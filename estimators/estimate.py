"""
Estimates
"""
from types import MethodType
from typing import Callable

from estimators.features import Feature


class Estimate:

    def __init__(self, estimation):
        self.estimation = estimation
        self.inputs = []
        self.targets = []
        self.idFunction = None

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
        self.inputs.append((name, feature, function))

    def _addTarget(self, name: str, feature: Feature, function: Callable):
        self.targets.append((name, feature, function))

    def estimate(self, *args):
        for name, feature, function in self.inputs:
            value = function(*args)
        return [0] * len(self.targets)

    def collect(self, *args):
        for name, feature, function in self.targets:
            value = function(*args)


class SelectionTimeEstimate(Estimate):

    def __init__(self, estimation):
        super().__init__(estimation)
        self.targets.append(("time", Feature(), lambda x: 0))

    def estimate(self, *args):
        est = super().estimate(*args)
        return est[0]


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
