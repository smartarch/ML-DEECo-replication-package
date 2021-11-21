class PointNotOnMapError(Exception):
    """Exception raised for errors in the input Point.

    Attributes:
        dim -- the dimmension as X or Y
    """

    def __init__(self, dim):
        self.message = f"{dim} is not on the map, please enter a value  > 0."
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'