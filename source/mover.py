class Mover:
    """
        class for moving objects
    """
    

    def __init__ (self,
                    currentPoint,
                    targetPoint,
                    speed = 1):
        self.currentLocation = currentPoint
        self.targetLocation = targetPoint
        self.speed = speed

    def moveWithSpeed(mover, speed):
        if mover== 0:
            return 0
        else:
            if abs(mover)<speed:
                speed = abs(mover)
            return int((abs(mover)/mover)*speed)
    
    def move(self):
        if self.currentLocation == self.targetLocation:
            return self.currentLocation

        x_mover, y_mover = self.currentLocation - self.targetLocation
        
        self.currentLocation.x -= Mover.moveWithSpeed(x_mover,self.speed)
        self.currentLocation.y -= Mover.moveWithSpeed(y_mover,self.speed)
        return self.currentLocation

    def __str__(self):
        return "default mover"

class BirdMover(Mover):

    def __init__ (self,bird):
        super().__init__ (bird.location,
                        bird.target,
                        bird.speed )
        self.bird = bird
    def move(self):
        super().move()
        self.bird.location = self.currentLocation

    def __str__(self):
        return "birMover"