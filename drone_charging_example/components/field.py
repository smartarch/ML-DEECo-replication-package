import math
import random

from world import ENVIRONMENT

from ml_deeco.simulation import Point


class Field:
    """
        A Field that the simulation is running on.

        This defines an Area, which is technically a set of points.
        The set of points consist of 4 doubles as [x1, y1, x2, y2]

            (x1,y1) .__________
                    |          |
                    |__________|.(x2,y2)

        Static Count for the Fields
    """

    # Field counter
    Count = 0

    topLeft: Point
    bottomRight: Point

    def __init__(self, pointLists):

        self.droneRadius = ENVIRONMENT.droneRadius
        Field.Count = Field.Count + 1
        self.id = f"FIELD_{Field.Count}"
        self.topLeft = Point(pointLists[0], pointLists[1])
        self.bottomRight = Point(pointLists[2], pointLists[3])

        self.places = []
        self.protectingDrones = {}
        self.memory = {}
        self.crops = {}  # for birds
        self.damaged = []  # for vis
        self.damage = 0

        for i in range(self.topLeft.x + self.droneRadius, self.bottomRight.x, round(self.droneRadius )):
            for j in range(self.topLeft.y + self.droneRadius, self.bottomRight.y, round(self.droneRadius)):
                self.places.append(Point(i, j))

        for i in range(self.topLeft.x, self.bottomRight.x):
            for j in range(self.topLeft.y, self.bottomRight.y):
                self.crops[(i, j)] = 0
        self.allCrops = len(self.crops)

    def locationPoints(self):
        points = []
        for x in range(self.topLeft.x, self.bottomRight.x):
            for y in range(self.topLeft.y, self.bottomRight.y):
                points.append(Point(x, y))

        return points

    # def randomPointOnField(self):
    #     return [randint(self.topLeft.x, self.bottomRight.x-1),randint(self.topLeft.y, self.bottomRight.y-1)]

    # a function to call and set all field points
    def isPointOnField(self, point):
        return self.topLeft.x <= point.x < self.bottomRight.x and \
               self.topLeft.y <= point.y < self.bottomRight.y

    def closestDistanceToDrone(self, drone):
        distances = []
        for place in self.places:
            dx = place.x - drone.location.x
            dy = place.y - drone.location.y
            distances.append(math.sqrt(dx * dx + dy * dy))

        return min(distances)

    def assingPlace(self, drone):
        if drone not in self.protectingDrones:
            if drone not in self.memory:
                listOfEmptyPlaces = [place for place in self.places if place not in [self.memory[d] for d in self.memory]]
                if len(listOfEmptyPlaces) <= 0:
                    self.protectingDrones[drone] = random.choice(self.places)
                else:
                    self.protectingDrones[drone] = min(listOfEmptyPlaces, key=lambda p: p.distance(drone.location))
                self.memory[drone] = self.protectingDrones[drone]
            else:
                self.protectingDrones[drone] = self.memory[drone]

        return self.protectingDrones[drone]

    def unassign(self, drone):
        if drone in self.protectingDrones:
            del self.protectingDrones[drone]
            if drone.state == 5:  # terminated
                del self.memory[drone]

    def randomLocation(self):
        return Point.random(self.topLeft.x, self.topLeft.y, self.bottomRight.x, self.bottomRight.y)

    # def closestDistanceToDrone (self,drone):
    #     minDistance = self.closestZoneToDrone(drone)
    #     return minDistance

    def randomPlaces(self, protectors):
        places = []
        # lenZones = len(self.zones)
        # interval = 1 if protectors > lenZones else int(lenZones/protectors)
        for i in range(protectors):
            randomZone = random.choice(self.places)
            places.append(Point(randomZone.x, randomZone.y))
        return places

    def __str__(self):
        return f"{self.id},{self.topLeft},{self.bottomRight}"

    def locationDamaged(self, location):
        p = (location.x, location.y)
        if p in self.crops:
            self.crops[p] = self.crops[p] + 1
            if self.crops[p] == 2:
                del self.crops[p]
                self.damaged.append(Point(location.x, location.y))
                self.damage = self.damage + 1

    def randomUndamagedCorp(self):
        if len(self.crops) == 0:
            return None
        safe = random.choice([p for p in self.crops])
        return Point(safe[0], safe[1])
