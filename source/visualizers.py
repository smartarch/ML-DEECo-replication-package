from PIL import Image , ImageFont,ImageDraw
import numpy as np
import pandas as pd
from random import randint
from components import DroneState

COLORS ={
    'drone': [77, 148, 255], 	
    'bird': [255, 20, 102],
    'field': [0, 102, 0],
    'charger': [204, 204, 0], 
    'grid': [255, 255, 255],
    'text' : (237, 230, 211), 
}

SIZES = {
    'drone': 4,
    'bird': 4,
    'field': 5,
    'charger': 5, 
}



class Visualizer:
    

    def __init__ (self, world):
        self.world = world
        self.cellSize =  SIZES['field']
        self.width = world.mapWidth *self.cellSize

        self.height = world.mapHeight *self.cellSize
        
        self.images = []
        self.grid = {}
        #self.textFont = ImageFont.truetype("sans-serif.ttf", 16)
        

    # change to fill for a  better efferent method
    def drawRectangle(self,canvas,point,component):
        
        startY = (point[1])*self.cellSize
        endY = startY+SIZES[component]
        startX = (point[0])*self.cellSize
        endX = startX+SIZES[component]
        for i in range(startY,endY):
            for j in range(startX,endX):
                canvas[i][j] = COLORS[component]
        return (startX+(endX-startX)/2,startY+(endY-startY)/2)
        
    def drawCircle(self,drawObject,rectangelMap):
        x1= rectangelMap[0] *self.cellSize
        y1= rectangelMap[1] *self.cellSize
        x2= rectangelMap[2] *self.cellSize
        y2= rectangelMap[3] *self.cellSize

        drawObject.ellipse((x1,y1,x2,y2), outline ='blue')


    def drawFields(self):
        self.background = np.zeros(
                                (self.height ,
                                self.width, 3 )) # 3 for RGB and H for unsigned short

        for field in self.world.fields:
            filedPoints = field.locationPoints()
            self.grid[field] = filedPoints
            for point in filedPoints:
                self.drawRectangle(self.background ,point,'field')



    def drawComponents (self, iteration=0):

        array = np.array(self.background ,copy=True)

        for bird in self.world.birds:
            self.grid[bird] = self.drawRectangle(array,bird.location,'bird')
        
        for drone in self.world.drones:
            self.grid[drone] = self.drawRectangle(array,drone.location,'drone')

        for charger in self.world.chargers:
            self.drawRectangle(array,charger.location,'charger')

        image = Image.fromarray(array.astype(np.uint8), 'RGB')
        draw = ImageDraw.Draw(image)
        for drone in self.world.drones:
            if drone.state == DroneState.PROTECTING:
                self.drawCircle(draw,drone.protectRadius())
            draw.text((self.grid[drone]),f"{drone.battery -  drone.energyNeededToMoveToCharger():.2f}",COLORS['text'])   


        titleText = f"iteration: {iteration}"
        draw.text((self.width-200,20),titleText,COLORS['text'])   
        self.images.append(image)


    def createAnimation(self,filename):
        self.images[0].save(filename, save_all=True, append_images=self.images[1:])