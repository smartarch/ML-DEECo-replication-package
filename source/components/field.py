from source.components.point import Point
import random
import math
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
    World = None

    topLeft : Point
    bottomRight : Point

    def __init__ (
                    self,
                    pointLists,
                    **kwargs):

        self.radius = 5 if 'radius' not in kwargs else kwargs['radius']
        Field.Count = Field.Count +1
        self.id = f"FIELD_{Field.Count}"
        self.topLeft = Point(pointLists[0],pointLists[1])
        self.bottomRight = Point(pointLists[2],pointLists[3])

        self.zones = []
        # new approach: how many protecting zones there are
        for x in range(self.topLeft[0],self.bottomRight[0],self.radius):
            for y in range(self.topLeft[1],self.bottomRight[1],self.radius):
                self.zones .append([x+ self.radius/2,y+ self.radius/2 ])
    
            
    @property
    def places(self):
        return self.locationPoints()

    # return all locations
    def locationPoints(self):
        points = []
        for x in range(self.topLeft.x,self.bottomRight.x):
            for y in range(self.topLeft.y,self.bottomRight.y):
                points.append ([x,y])

        return points

    def randomPointOnField(self):
        return [randint(self.topLeft.x, self.bottomRight.x-1),randint(self.topLeft.y, self.bottomRight.y-1)]
    
    # a function to call and set all field points
    def isPointOnField (self,point):
        return (point.x >= self.topLeft.x and point.x < self.bottomRight.x) and (point.y >= self.topLeft.y and point.y < self.bottomRight.y)

    def closestZoneToDrone(self,drone):
        distances = []
        for zone in self.zones:
            dx = zone[0] - drone.location[0]
            dy = zone[1] - drone.location[1]
            distances.append(math.sqrt(dx * dx + dy * dy))

        return min(distances)

    def closestDistanceToDrone (self,drone):
        minDistance = self.closestZoneToDrone(drone)
        return minDistance

    def randomZones(self,protectors):
        places = []
        #lenZones = len(self.zones)
        #interval = 1 if protectors > lenZones else int(lenZones/protectors)
        for i in range(protectors):
            randomZone = random.choice(self.zones)
            places.append (Point(int(randomZone[0]),int(randomZone[1])))
        return places

    def __str__ (self):
        return f"{self.id},{self.topLeft},{self.bottomRight}"
        
