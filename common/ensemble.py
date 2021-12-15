import operator
from collections import defaultdict
from typing import Dict, Any


class someOf():
    counter = 0

    def __init__(self, compClass):
        self.id = someOf.counter
        someOf.counter += 1

        self.compClass = compClass

        self.cardinalityFn = None
        self.selectFn = None
        self.priorityFn = None

        self.selections: Dict[Ensemble, Any] = defaultdict(lambda: None)

    def __get__(self, instance, owner):
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

    def execute(self, instance, allComponents, otherEnsembles):
        assert(self.cardinalityFn is not None)
        assert(self.selectFn is not None)

        self.selections[instance] = []
        cardinality = self.cardinalityFn(instance)
        if isinstance(cardinality, tuple):
            cardinalityMin, cardinalityMax = cardinality
        else:
            cardinalityMin = cardinality
            cardinalityMax = cardinality

        for idx in range(cardinalityMax):
            sel = [(self.priorityFn(instance, comp), comp) for comp in allComponents if isinstance(comp, self.compClass) and self.selectFn(instance, comp, otherEnsembles)]
            if len(sel) > 0:
                _, comp = max(sel, key=operator.itemgetter(0))
                self.selections[instance].append(comp)

        if len(self.selections[instance]) < cardinalityMin:
            return False

        return True


class oneOf(someOf):
    def __init__(self, compClass):
        super().__init__(compClass)
        self.cardinalityFn = lambda inst: 1

    def __get__(self, instance, owner):
        sel = super().__get__(instance, owner)
        return sel[0]


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
    
    def actuate(self, verbose):
        pass

    def priority(self) -> float:
        """Bigger number -> earlier materialization"""
        return 1

    def __lt__(self, other):
        return self.priority() > other.priority()



