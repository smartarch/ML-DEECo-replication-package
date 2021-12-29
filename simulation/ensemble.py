import operator
from collections import defaultdict
from typing import Dict, Any, TYPE_CHECKING, Callable, List

from estimators.estimate import TimeEstimate, ListWithTimeEstimate
if TYPE_CHECKING:
    from estimators.estimator import Estimator


class someOf():
    counter = 0

    def __init__(self, compClass):
        self.id = someOf.counter
        someOf.counter += 1

        self.compClass = compClass
        self.onMaterialized: List[Callable] = []

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

    def materialized(self, instance):
        """Called when the ensemble is materialized."""
        for f in self.onMaterialized:
            f(self, instance)

    def withSelectionTimeEstimate(self):
        return someOfWithSelectionTimeEstimate(self.compClass)

    def withTimeToMembershipInOtherEnsembleEstimate(self):
        return someOfWithTimeToMembershipInOtherEnsembleEstimate(self.compClass)


class someOfWithSelectionTimeEstimate(someOf):

    def __init__(self, compClass):
        super().__init__(compClass)
        self.onMaterialized.append(self.collectTargets)
        self.timeEstimate = TimeEstimate()

    def using(self, estimator: 'Estimator'):
        self.timeEstimate.using(estimator)
        return self

    def select(self, selectFn):
        def newSelectFn(instance, comp, otherEnsembles):
            select = selectFn(instance, comp, otherEnsembles)
            if select:
                self.timeEstimate.collectInputs(instance, comp)
            return select

        self.selectFn = newSelectFn
        return self

    def get(self, instance, owner):
        sel = super().get(instance, owner)
        if isinstance(sel, list):
            sel = ListWithTimeEstimate(sel)
        sel.timeEstimate = self.timeEstimate
        return sel

    def collectTargets(self, _self, instance):
        """Called when the ensemble is materialized."""
        selected = self.get(instance, None)
        for comp in selected:
            self.timeEstimate.collectTargets(instance, comp)

    def selectComponents(self, instance, allComponents, otherEnsembles):
        filteredComponents = self.filterComponentsByType(instance, allComponents)
        self.timeEstimate.cacheEstimates(instance, filteredComponents)
        filteredComponents = self.filterPreviouslySelectedComponents(instance, filteredComponents)
        filteredComponents = self.filterBySelectFunction(instance, filteredComponents, otherEnsembles)
        return self.assignPriority(instance, filteredComponents)


class someOfWithTimeToMembershipInOtherEnsembleEstimate(someOf):

    def __init__(self, compClass):
        super().__init__(compClass)
        self.onMaterialized.append(self.collectInputs)
        self.timeToMembershipEstimate = TimeEstimate()
        self.timeToMembershipEstimate.inputsIdFunction = lambda instance, comp: comp
        self.timeToMembershipEstimate.targetsIdFunction = self.timeToMembershipEstimate.inputsIdFunction

    def using(self, estimator: 'Estimator'):
        self.timeToMembershipEstimate.using(estimator)
        return self

    def get(self, instance, owner):
        sel = super().get(instance, owner)
        if isinstance(sel, list):
            sel = ListWithTimeEstimate(sel)
        sel.timeEstimate = self.timeToMembershipEstimate
        return sel

    def collectInputs(self, _self, instance):
        """Called when the ensemble is materialized."""
        selected = self.get(instance, None)
        for comp in selected:
            self.timeToMembershipEstimate.collectInputs(instance, comp)

    def collectTargets(self, other, instance):
        """Called when the other ensemble is materialized."""
        selected = other.get(instance, None)
        for comp in selected:
            self.timeToMembershipEstimate.collectTargets(instance, comp)

    def selectComponents(self, instance, allComponents, otherEnsembles):
        filteredComponents = self.filterComponentsByType(instance, allComponents)
        self.timeToMembershipEstimate.cacheEstimates(instance, filteredComponents)
        filteredComponents = self.filterPreviouslySelectedComponents(instance, filteredComponents)
        filteredComponents = self.filterBySelectFunction(instance, filteredComponents, otherEnsembles)
        return self.assignPriority(instance, filteredComponents)

    def bindTo(self, other):
        other.onMaterialized.append(self.collectTargets)
        # other.timeEstimate = self.timeEstimate


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

        if allOk:
            for fld in compFields:
                fld.materialized(self)
                
        return allOk
    
    def actuate(self):
        pass

    def priority(self) -> float:
        """Bigger number -> earlier materialization"""
        return 1

    def __lt__(self, other):
        return self.priority() > other.priority()



