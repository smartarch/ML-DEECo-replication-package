"""
Estimates
"""
from enum import Enum, auto
from collections import namedtuple, defaultdict
from types import MethodType
from typing import Callable, List, TYPE_CHECKING
import numpy as np

from estimators.features import Feature
from simulation.world import WORLD

if TYPE_CHECKING:
    from estimators.estimation import Estimation


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

    def collectRecordInputs(self, recordId, x, extra=None, force_replace=False):
        if recordId not in self._records or force_replace:
            self._records[recordId] = []

        records = self._records[recordId]
        if self._mode == DataCollectorMode.All:
            records.append((x, extra))
        elif self._mode == DataCollectorMode.First:
            if len(records) == 0:
                records.append((x, extra))
        elif self._mode == DataCollectorMode.Last:
            if len(records) == 0:
                records.append((x, extra))
            else:
                records[0] = (x, extra)

    def collectRecordTargets(self, recordId, y):
        if recordId not in self._records:
            raise KeyError(f"RecordId '{recordId}' not found. The record inputs must be collected first using the 'collectRecordInputs' method.")

        records = self._records[recordId]
        del self._records[recordId]

        for x, extra in records:
            self.x.append(x)
            if callable(y):
                self.y.append(y(x, extra))
            else:
                self.y.append(y)

    def clear(self):
        self.x = []
        self.y = []
        self._records = {}


class Estimate:

    def __init__(self):
        self.estimation: 'Estimation' = None
        self.inputs: List[BoundFeature] = []
        self.extras: List[BoundFeature] = []
        self.targets: List[BoundFeature] = []
        self.inputsIdFunction = None
        self.targetsIdFunction = None
        self.inputsFilterFunctions: List[Callable] = []
        self.targetsFilterFunctions: List[Callable] = []
        self.dataCollector = DataCollector()

    def using(self, estimation: 'Estimation'):
        self.estimation = estimation
        estimation.assignEstimate(self)
        return self

    def check(self):
        """Checks whether the estimate is initialized properly."""
        assert self.estimation is not None, "No estimation assigned, use the 'using' method to assign an estimation."
        assert self.inputsIdFunction is not None, f"{self.estimation.name}: 'inputsId' function not specified."
        assert self.targetsIdFunction is not None, f"{self.estimation.name}: 'targetsId' function not specified."
        assert len(self.inputs) > 0, f"{self.estimation.name}: No inputs specified."
        assert len(self.targets) > 0, f"{self.estimation.name}: No targets specified."

    def input(self, feature=None):
        """Defines an input feature"""
        if feature is None:
            feature = Feature()

        def addInputFunction(function):
            self._addInput(function.__name__, feature, function)
            return function

        return addInputFunction

    def extra(self, function):
        """Defines an extra input feature – not given to the prediction model."""
        self._addExtra(function.__name__, function)
        return function

    def target(self, feature=None):
        """Defines a target value"""
        if feature is None:
            feature = Feature()

        def addTargetFunction(function):
            self._addTarget(function.__name__, feature, function)
            return function

        return addTargetFunction

    def inputsId(self, function):
        self.inputsIdFunction = function
        return function

    def targetsId(self, function):
        self.targetsIdFunction = function
        return function

    def inputsFilter(self, function):
        self.inputsFilterFunctions.append(function)
        return function

    def targetsFilter(self, function):
        self.targetsFilterFunctions.append(function)
        return function

    def _addInput(self, name: str, feature: Feature, function: Callable):
        self.inputs.append(BoundFeature(name, feature, function))

    def _addExtra(self, name: str, function: Callable):
        self.extras.append(BoundFeature(name, None, function))

    def _addTarget(self, name: str, feature: Feature, function: Callable):
        self.targets.append(BoundFeature(name, feature, function))

    def inTimeSteps(self, timeSteps):
        """Automatically collect the data with fixed time difference between inputs and targets."""
        self.targetsFilterFunctions.append(lambda *args: WORLD.currentTimeStep > timeSteps)
        self.inputsIdFunction = lambda *args: (*args, WORLD.currentTimeStep)
        self.targetsIdFunction = lambda *args: (*args, WORLD.currentTimeStep - timeSteps)
        return self

    def bind(self, function):
        def collectAndRun(*args, **kwargs):
            result = function(*args, **kwargs)
            self.collectInputs(*args)
            self.collectTargets(*args)
            return result
        return collectAndRun

    def estimate(self, *args, collect=False):

        x = self.generateRecord(*args)
        if collect:
            self.collectInputs(*args, x=x)

        prediction = self.estimation.predict(x)

        if len(prediction) == 1:
            prediction = prediction[0]
        return prediction.tolist()

    def generateRecord(self, *args):
        record = []
        for name, feature, function in self.inputs:
            value = function(*args)
            value = feature.preprocess(value)
            record.append(value)
        return np.concatenate(record)

    def collectInputs(self, *args, x=None, id=None):
        for f in self.inputsFilterFunctions:
            if not f(*args):
                return

        if x is None:
            x = self.generateRecord(*args)

        extra = {
            name: function(*args)
            for name, _, function in self.extras
        }

        recordId = id if id is not None else self.inputsIdFunction(*args)
        self.dataCollector.collectRecordInputs(recordId, x, extra)

    def generateTargets(self, *args):
        record = []
        for name, feature, function in self.targets:
            value = function(*args)
            value = feature.preprocess(value)
            record.append(value)
        return np.concatenate(record)

    def collectTargets(self, *args, id=None):
        for f in self.targetsFilterFunctions:
            if not f(*args):
                return

        y = self.generateTargets(*args)

        recordId = id if id is not None else self.targetsIdFunction(*args)
        self.dataCollector.collectRecordTargets(recordId, y)

    def getData(self, clear=True):
        x, y = self.dataCollector.x, self.dataCollector.y
        if clear:
            self.dataCollector.clear()
        return x, y


class SelectionTimeEstimate(Estimate):

    def __init__(self):
        super().__init__()
        self.inputsIdFunction = lambda instance, comp: (instance, comp)
        self.targetsIdFunction = self.inputsIdFunction
        self.timeFunc = self.time(lambda *args: WORLD.currentTimeStep)

        self.targets = [BoundFeature("time", Feature(), None)]

        self.estimateCache = defaultdict(dict)

    def time(self, function):
        self.timeFunc = function
        self.extras = [BoundFeature("time", Feature(), self.timeFunc)]
        return function

    def generateTargets(self, *args):
        currentTimeStep = self.timeFunc(*args)

        def timeDifference(x, extra):
            difference = currentTimeStep - extra['time']
            return np.array([difference])

        return timeDifference

    def estimate(self, *args, collect=False):
        instance, comp = args
        if comp in self.estimateCache[instance]:
            return self.estimateCache[instance][comp]
        else:
            print("WARNING: estimate not cached, computing it again")
            return super().estimate(*args)

    def cacheEstimates(self, instance, comps):
        records = np.array([self.generateRecord(instance, comp) for comp in comps])
        predictions = self.estimation.predictBatch(records)

        self.estimateCache[instance] = {
            comp: prediction[0]
            for comp, prediction in zip(comps, predictions)
        }


class ListWithSelectionTimeEstimate(list):
    selectionTimeEstimate = None


# def addSelectionTimeEstimate(compSelector, estimation):
#     compSelector.selectionTimeEstimate = SelectionTimeEstimate(estimation)
#     origGet = compSelector.get
#     origSelectFn = compSelector.selectFn
#     origExecute = compSelector.execute
#
#     def newGet(self, instance, owner):
#         sel = origGet(instance, owner)
#         if isinstance(sel, list):
#             sel = ListWithSelectionTimeEstimate(sel)
#         sel.selectionTimeEstimate = compSelector.selectionTimeEstimate
#         return sel
#
#     def newSelectFn(instance, comp, otherEnsembles):
#         select = origSelectFn(instance, comp, otherEnsembles)
#         if select:
#             compSelector.selectionTimeEstimate.collectInputs(comp)
#         return select
#
#     # TODO(MT): modify execute to collect training data
#
#     compSelector.get = MethodType(newGet, compSelector)
#     compSelector.selectFn = newSelectFn
#     return compSelector
