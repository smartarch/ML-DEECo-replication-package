import operator
from collections import defaultdict
from typing import Dict, Any

from estimators.estimate import SelectionTimeEstimate, ListWithSelectionTimeEstimate


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

    def filterComponents(self, instance, allComponents, otherEnsembles):
        return [(self.priorityFn(instance, comp), comp) for comp in allComponents if
                isinstance(comp, self.compClass) and
                comp not in self.selections[instance]]

    def selectComponents(self, instance, allComponents, otherEnsembles):
        filteredComponents = self.filterComponents(instance, allComponents, otherEnsembles)
        return [(priority, comp) for priority, comp in filteredComponents if
                self.selectFn(instance, comp, otherEnsembles)]

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
        pass

    def withSelectionTimeEstimate(self, estimation):
        return someOfWithSelectionTimeEstimate(self.compClass, estimation)


class someOfWithSelectionTimeEstimate(someOf):

    def __init__(self, compClass, estimation):
        super().__init__(compClass)
        self.selectionTimeEstimate = SelectionTimeEstimate(estimation)

    def select(self, selectFn):
        def newSelectFn(instance, comp, otherEnsembles):
            select = selectFn(instance, comp, otherEnsembles)
            if select:
                self.selectionTimeEstimate.collectInputs(instance, comp)
            return select

        self.selectFn = newSelectFn
        return self

    def get(self, instance, owner):
        sel = super().get(instance, owner)
        if isinstance(sel, list):
            sel = ListWithSelectionTimeEstimate(sel)
        sel.selectionTimeEstimate = self.selectionTimeEstimate
        return sel

    def materialized(self, instance):
        """Called when the ensemble is materialized."""
        selected = self.get(instance, None)
        for comp in selected:
            self.selectionTimeEstimate.collectTargets(instance, comp)

    def selectComponents(self, instance, allComponents, otherEnsembles):
        filteredComponents = self.filterComponents(instance, allComponents, otherEnsembles)
        self.selectionTimeEstimate.cacheEstimates(instance, [comp for priority, comp in filteredComponents])
        return [(priority, comp) for priority, comp in filteredComponents if
                self.selectFn(instance, comp, otherEnsembles)]


class oneOf(someOf):
    def __init__(self, compClass):
        super().__init__(compClass)
        self.cardinalityFn = lambda inst: 1

    def get(self, instance, owner):
        sel = super().get(instance, owner)
        return sel[0]


# TODO(MT): someOfWithSelectionTimeEstimate


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



