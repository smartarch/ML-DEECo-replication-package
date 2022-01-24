"""
Estimates
"""
from collections import namedtuple, defaultdict
from enum import Enum, auto
from typing import Callable, List, TYPE_CHECKING, Optional

import numpy as np

from ml_deeco.estimators import Feature, TimeFeature
from ml_deeco.simulation import SIMULATION_GLOBALS

if TYPE_CHECKING:
    from ml_deeco.estimators import Estimator


BoundFeature = namedtuple('BoundFeature', ('name', 'feature', 'function'))


class DataCollectorMode(Enum):
    First = auto()  # keep only the first record for each recordId
    Last = auto()   # keep only the last record for each recordId
    All = auto()    # keep all records for each recordId


class DataCollector:

    def __init__(self, begin=DataCollectorMode.All):
        self._records = {}
        self._begin = begin
        self.x = []
        self.y = []

    def collectRecordInputs(self, recordId, x, extra=None, force_replace=False):
        if recordId not in self._records or force_replace:
            self._records[recordId] = []

        records = self._records[recordId]
        if self._begin == DataCollectorMode.All:
            records.append((x, extra))
        elif self._begin == DataCollectorMode.First:
            if len(records) == 0:
                records.append((x, extra))
        elif self._begin == DataCollectorMode.Last:
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
    """
    Implementation of the value estimate (both regression and classification). Predicts a future value based on current observations.
    """

    def __init__(self, **dataCollectorKwargs):
        # noinspection PyTypeChecker
        self.estimator: 'Estimator' = None
        self.inputs: List[BoundFeature] = []
        self.extras: List[BoundFeature] = []
        self.targets: List[BoundFeature] = []
        self.inputsIdFunction = lambda *args: (*args,)
        self.targetsIdFunction = lambda *args: (*args,)
        self.inputsFilterFunctions: List[Callable] = []
        self.targetsFilterFunctions: List[Callable] = []
        self.dataCollector = DataCollector(**dataCollectorKwargs)

    def using(self, estimator: 'Estimator'):
        """Assigns an estimator to the estimate."""
        self.estimator = estimator
        estimator.assignEstimate(self)
        return self

    def check(self):
        """Checks whether the estimate is initialized properly."""
        assert self.estimator is not None, "No estimator assigned, use the 'using' method to assign an estimator."
        assert self.inputsIdFunction is not None, f"{self.estimator.name}: 'inputsId' function not specified."
        assert self.targetsIdFunction is not None, f"{self.estimator.name}: 'targetsId' function not specified."
        assert len(self.inputs) > 0, f"{self.estimator.name}: No inputs specified."
        assert len(self.targets) > 0, f"{self.estimator.name}: No targets specified."

    # decorators (definition of inputs and outputs)

    def input(self, feature: Optional[Feature] = None):
        """Defines an input feature."""
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

    def target(self, feature: Optional[Feature] = None):
        """Defines a target value."""
        if feature is None:
            feature = Feature()

        def addTargetFunction(function):
            self._addTarget(function.__name__, feature, function)
            return function

        return addTargetFunction

    def inputsId(self, function):
        """Defines the function for matching the inputs with according targets. Unless there is a specific need for modifying the default behavior, do not use this decorator."""
        self.inputsIdFunction = function
        return function

    def targetsId(self, function):
        """Defines the function for matching the targets with according inputs. Unless there is a specific need for modifying the default behavior, do not use this decorator."""
        self.targetsIdFunction = function
        return function

    def inputsValid(self, function):
        """Guard for detecting whether the inputs are valid and can be used for training. Use this as a decorator."""
        self.inputsFilterFunctions.append(function)
        return function

    def targetsValid(self, function):
        """Guard for detecting whether the targets are valid and can be used for training. Use this as a decorator."""
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
        self.targetsFilterFunctions.append(lambda *args: SIMULATION_GLOBALS.currentTimeStep >= timeSteps)
        self.inputsIdFunction = lambda *args: (*args, SIMULATION_GLOBALS.currentTimeStep)
        self.targetsIdFunction = lambda *args: (*args, SIMULATION_GLOBALS.currentTimeStep - timeSteps)
        return self

    # estimation

    # TODO(MT): remove the collect parameter
    def estimate(self, *args, collect=False):
        """Computes the estimate (based on the current values of the attributes)."""

        x = self.generateRecord(*args)
        if collect:
            self.collectInputs(*args, x=x)

        prediction = self.estimator.predict(x)

        return self.generateOutputs(prediction)

    def generateRecord(self, *args):
        record = []
        for name, feature, function in self.inputs:
            value = function(*args)
            value = feature.preprocess(value)
            record.append(value)
        return np.concatenate(record)

    def generateOutputs(self, prediction):
        # if we have only one target, return just the value
        if len(self.targets) == 1:
            return self.targets[0][1].postprocess(prediction)

        # otherwise, return a dictionary with all the targets
        output = {}
        currentIndex = 0
        for name, feature, _ in self.targets:
            width = feature.getNumFeatures()
            values = prediction[currentIndex:currentIndex + width]
            output[name] = feature.postprocess(values)
            currentIndex += width

        return output

    def __get__(self, instance, owner):
        if instance is None:
            return self

        def estimate(*args):
            return self.estimate(instance, *args)

        return estimate

    # data collection

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


class TimeEstimate(Estimate):
    """
    Implementation of the time-to-condition estimate.
    """

    def __init__(self, **dataCollectorKwargs):
        super().__init__(**dataCollectorKwargs)
        self.timeFunc = self.time(lambda *args: SIMULATION_GLOBALS.currentTimeStep)

        self.targets = [BoundFeature("time", TimeFeature(), None)]
        self.userTargets = []
        self.conditionFunctions = []

        self.estimateCache = defaultdict(dict)

    def time(self, function):
        """Defines how to measure time for the time-to-condition estimate. The default uses the current time step of the simulation, so if the simulation is run using our `run_simulation`, there is no need to overriding the default behavior using this function."""
        self.timeFunc = function
        self.extras = [BoundFeature("time", TimeFeature(), self.timeFunc)]
        return function

    def _addTarget(self, name: str, feature: Feature, function: Callable):
        self.userTargets.append(BoundFeature(name, feature, function))

    def condition(self, function):
        """Defines the condition for the time-to-condition estimate. If multiple conditions are defined, they are considered in an "and" manner."""
        self.conditionFunctions.append(function)
        return function

    def collectTargets(self, *args, id=None):
        # TODO(MT): return back to using a condition without the targets and remove this
        userTargets = [function(*args) for name, feature, function in self.userTargets]
        for f in self.conditionFunctions:
            argCount = f.__code__.co_argcount
            missingArgs = argCount - len(userTargets)
            # args[0] is the component/ensemble instance (`self` of the condition method)
            # this way, the condition can be either static, or bound and both will work
            if not f(*args[:missingArgs], *userTargets):
                return
        super().collectTargets(*args, id=id)

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
        """Computes the estimates for all components in a batch at the same time and caches the results."""
        records = np.array([self.generateRecord(instance, comp) for comp in comps])
        predictions = self.estimator.predictBatch(records)

        self.estimateCache[instance] = {
            comp: prediction[0]
            for comp, prediction in zip(comps, predictions)
        }


class ListWithEstimate(list):
    estimate = None
