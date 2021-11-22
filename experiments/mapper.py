"""
    This tool creates a map from an image
    PNG/JPG --> YAML
    it converts:

    RED (255,0,0) dots to CHARGERS
    GREEN (0,255,0) dots to DRONES
    BLUE (0,0,255) rectangles to FIELDS
    BLACK (0,0,0) line as radius
    the image Width and Heigh are considred to be the mapWidth and mapHeight
    the rest of information are stated in terms of variables

"""

COLORS = [
    "empty",
    "chargers",
    "fields",
    "drone",
    "droneRadius",
]

data = {
    "birds": 10,
    "maxSteps": 500,
    "droneRadius": 5,
    "birdSpeed": 1 ,
    "droneSpeed": 1,
    "droneMovingEnergyConsumption": 0.01,
    "droneProtectingEnergyConsumption": 0.005,
    "chargingRate": 0.2,
    "drones" : [],
    "fields" : [],
    "chargers" : [],
    "mapWidth" : 0,
    "mapHeight" : 0,
    "droneRadius": 5,
}

imageFile = "mapTest.png"
yamlFile = "expTest.yaml"

from PIL import Image
import numpy as np



def detectColor(chanels):
    if sum(chanels) > 200*len(chanels):
        return 0 # empty

    for i in range(chanels):
        if chanels[i]>200:
            return i+1 # red, green or blue

    return 4 # black
        

    
    

def main():
    im = Image.open(imageFile)
    array = np.array(im)
    width, height = im.size
    for i in range(height):
        for j in range(width):
            pass

if __name__ == "__main__":
    main()


