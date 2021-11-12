from source.components.point import Point

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
                    pointLists):
        Field.Count = Field.Count +1
        self.id = f"FIELD_{Field.Count}"
        self.topLeft = Point(pointLists[0],pointLists[1])
        self.bottomRight = Point(pointLists[2],pointLists[3])

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

    def __str__ (self):
        return f"{self.id},{self.topLeft},{self.bottomRight}"
        
