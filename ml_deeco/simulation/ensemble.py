import operator
from collections import defaultdict
from typing import Dict, Any, TYPE_CHECKING

from ml_deeco.estimators.estimate import TimeEstimate, ListWithEstimate, Estimate

if TYPE_CHECKING:
    from ml_deeco.estimators.estimator import Estimator


class someOf():
    counter = 0

    def __init__(self, compClass):
        self.id = someOf.counter
        someOf.counter += 1

        self.compClass = compClass

        self.cardinalityFn = None
        self.selectFn = None
        self.priorityFn = lambda _ens, _comp: 0

        self.selections: Dict[Ensemble, Any] = defaultdict(lambda: None)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.get(instance, owner)

    def get(self, instance, owner):
        return self.selections[instance]

    def cardinality(self, cardinalityFn):
        self.cardinalityFn = cardinalityFn
        return self

    def select(self, selectFn):
        self.selectFn = selectFn
        return self

    def priority(self, priorityFn):
        """Bigger number -> earlier selection"""
        self.priorityFn = priorityFn
        return self

    def reset(self, instance):
        self.selections[instance] = None

    def filterComponentsByType(self, instance, allComponents):
        return [comp for comp in allComponents if
                isinstance(comp, self.compClass)]

    def filterPreviouslySelectedComponents(self, instance, components):
        return [comp for comp in components if
                comp not in self.selections[instance]]

    def filterBySelectFunction(self, instance, components, otherEnsembles):
        return [comp for comp in components if
                self.selectFn(instance, comp, otherEnsembles)]

    def assignPriority(self, instance, components):
        return [(self.priorityFn(instance, comp), comp) for comp in components]

    def selectComponents(self, instance, allComponents, otherEnsembles):
        filteredComponents = self.filterComponentsByType(instance, allComponents)
        filteredComponents = self.filterPreviouslySelectedComponents(instance, filteredComponents)
        filteredComponents = self.filterBySelectFunction(instance, filteredComponents, otherEnsembles)
        return self.assignPriority(instance, filteredComponents)

    def execute(self, instance, allComponents, otherEnsembles):
        assert(self.cardinalityFn is not None)
        assert(self.selectFn is not None)

        self.selections[instance] = []

        cardinality = self.cardinalityFn(instance)
        if isinstance(cardinality, tuple):
            cardinalityMin, cardinalityMax = cardinality
        else:
            cardinalityMin, cardinalityMax = cardinality, cardinality

        sel = self.selectComponents(instance, allComponents, otherEnsembles)
        for idx in range(cardinalityMax):
            if len(sel) > 0:
                priority, comp = max(sel, key=operator.itemgetter(0))
                self.selections[instance].append(comp)
                sel = self.selectComponents(instance, allComponents, otherEnsembles)

        if len(self.selections[instance]) < cardinalityMin:
            return False

        return True

    def withEstimate(self):
        return someOfWithEstimate(self.compClass, Estimate())

    def withTimeEstimate(self, **dataCollectorKwargs):
        return someOfWithEstimate(self.compClass, TimeEstimate(**dataCollectorKwargs))


class someOfWithEstimate(someOf):

    def __init__(self, compClass, estimate: 'Estimate'):
        super().__init__(compClass)
        self.estimate = estimate
        self.estimate.inputsIdFunction = lambda instance, comp: comp
        self.estimate.targetsIdFunction = self.estimate.inputsIdFunction

    def using(self, estimator: 'Estimator'):
        self.estimate.using(estimator)
        return self

    def inTimeSteps(self, timeSteps):
        self.estimate.inTimeSteps(timeSteps)
        return self

    def get(self, instance, owner):
        sel = super().get(instance, owner)
        if isinstance(sel, list):
            sel = ListWithEstimate(sel)

        def estimate(*args):
            return self.estimate.estimate(instance, *args)

        sel.estimate = estimate
        return sel

    def collectEstimateData(self, instance):
        selected = self.get(instance, type(instance))
        for comp in selected:
            self.estimate.collectInputs(instance, comp)
            self.estimate.collectTargets(instance, comp)

    def selectComponents(self, instance, allComponents, otherEnsembles):
        """Estimate caching for better performance."""
        filteredComponents = self.filterComponentsByType(instance, allComponents)
        self.estimate.cacheEstimates(instance, filteredComponents)
        filteredComponents = self.filterPreviouslySelectedComponents(instance, filteredComponents)
        filteredComponents = self.filterBySelectFunction(instance, filteredComponents, otherEnsembles)
        return self.assignPriority(instance, filteredComponents)


class oneOf(someOf):
    def __init__(self, compClass):
        super().__init__(compClass)
        self.cardinalityFn = lambda inst: 1

    def get(self, instance, owner):
        sel = super().get(instance, owner)
        return sel[0]


# TODO(MT): oneOf with Estimates


class Ensemble:

    def materialize(self, components, otherEnsembles):

        # sorts a list of ensembles that are type of someOf according to id, 
        compFields = sorted([fld for (fldName, fld) in type(self).__dict__.items() if not fldName.startswith('__') and isinstance(fld, someOf)], key=lambda fld: fld.id)
        allOk = True
        for fld in compFields:
            if not fld.execute(self, components, otherEnsembles):
                allOk = False
                break

        if not allOk:
            for fld in compFields:
                fld.reset(self)
                
        return allOk
    
    def actuate(self):
        pass

    def priority(self) -> float:
        """Bigger number -> earlier materialization"""
        return 1

    def __lt__(self, other):
        return self.priority() > other.priority()

    def collectEstimatesData(self):
        compWithEstimateFields = [fld for (fldName, fld) in type(self).__dict__.items() if not fldName.startswith('__') and isinstance(fld, someOfWithEstimate)]
        for field in compWithEstimateFields:
            field.collectEstimateData(self)
