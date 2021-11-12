from source.components.exceptions import PointNotOnMapError
class Point:
    """
        The class represents a point on the world.
        X and Y are values from 0 to 1, for instance 0.5 meaning at the center of map.
        The default values at the start of each Point is 0.5 and 0.5
        Please keep in mind that the X and Y must be a value, where  0 < value < 1
    """

    _x: float
    _y: float

    def __init__ (
                    self,
                    x,
                    y):
        self.x = x
        self.y = y

    @property
    def x (self):
        return self._x
    
    @x.setter
    def x(self, value):
        if value<0:
            raise PointNotOnMapError(value)
        self._x = value
    
    @property
    def y (self):
        return self._y
    
    @y.setter
    def y(self, value):
        if value<0:
            raise PointNotOnMapError(value)
        self._y = value

    def __sub__ (self, other):
        return self.x-other.x , self.y-other.y
    
    def __eq__(self, other):
        return self[0]==other[0] and self[1]==other[1]
    def __str__ (self):
        return f"{self._x},{self.y}"
    
    def __getitem__(self, index):
        if index==0:
            return self._x
        else:
            return self._y

    def random (maxWidth,maxHeight):
        return Point(randint(1,maxWidth-1),randint(1,maxHeight-1))


