from PIL import Image, ImageDraw
import numpy as np
from simulation.drone_state import DroneState
from simulation.world import ENVIRONMENT

COLORS = {
    'drone': [0, 0, 255],
    'bird': [255, 20, 102],
    'field': [206, 215, 193],
    'charger': [204, 204, 0],
    'grid': [255, 255, 255],
    'corp': [0, 0, 0],
    'text': (0, 0, 0),
    'line': [255,0,0],
}

SIZES = {
    'drone': 5,
    'bird': 4,
    'field': 10,
    'charger': 6,
    'corp': 10,
}

LEGEND_SIZE = 200
TEXT_MARGIN = 10


class Visualizer:

    def __init__(self, world):
        self.world = world
        self.cellSize = SIZES['field']
        self.width = ENVIRONMENT.mapWidth * self.cellSize + LEGEND_SIZE  # 150 for legends

        self.height = ENVIRONMENT.mapHeight * self.cellSize

        self.images = []
        self.grid = {}

    def drawRectangle(self, canvas, point, component):

        startY = (point.y) * self.cellSize
        endY = startY + SIZES[component]
        startX = (point.x) * self.cellSize
        endX = startX + SIZES[component]
        for i in range(int(startY), int(endY)):
            for j in range(int(startX), int(endX)):
                canvas[i][j] = COLORS[component]
        return (startX + (endX - startX) / 2, startY + (endY - startY) / 2)

    def drawCircle(self, drawObject, rectangelMap):
        x1 = rectangelMap[0] * self.cellSize
        y1 = rectangelMap[1] * self.cellSize
        x2 = rectangelMap[2] * self.cellSize
        y2 = rectangelMap[3] * self.cellSize

        drawObject.ellipse((x1, y1, x2, y2), outline='blue')

    def drawFields(self):
        self.background = np.zeros(
            (self.height,
             self.width, 3))  # 3 for RGB and H for unsigned short
        self.background.fill(255)
        for field in self.world.fields:
            filedPoints = field.locationPoints()
            self.grid[field] = filedPoints
            for point in filedPoints:
                self.drawRectangle(self.background, point, 'field')
        # draw a line
        legendStartPoint = self.width - LEGEND_SIZE
        for i in range(self.height):
            self.background[i][legendStartPoint] = COLORS['line']

    def getLegends(self):

        text = "-- WORLD STATUS --"
        text = f"{text}\niteration: {self.world.currentTimeStep + 1}"
        text = f"{text}\nalive drones: {len([drone for drone in self.world.drones if drone.state != DroneState.TERMINATED])}"
        text = f"{text}\nchargers: {len(self.world.chargers)}"
        text = f"{text}\ncharger capacity: {ENVIRONMENT.chargerCapacity}"
        text = f"{text}\nCharger Queues:"
        
        for charger in self.world.chargers:
            accepted = set(charger.acceptedDrones)
            waiting = set(charger.waitingDrones)
            potential = set(charger.potentialDrones)

            text = f"{text}\n-{charger.id}, C:{len(charger.chargingDrones)}, A:{len(accepted)}, W:{len(waiting - accepted)}, P:{len(potential - waiting - accepted)}"

            for drone in charger.chargingDrones:
                text = f"{text}\n--{drone.id}, b:{drone.battery:.2f} - C, t:{drone.timeToDoneCharging():.0f}"
            for drone in charger.acceptedDrones:
                text = f"{text}\n--{drone.id}, b:{drone.battery:.2f} - A, t:{drone.timeToDoneCharging():.0f}"
            for drone in waiting - accepted:
                text = f"{text}\n--{drone.id}, b:{drone.battery:.2f} - W, t:{drone.timeToDoneCharging():.0f}"
            for drone in potential - waiting - accepted:
                text = f"{text}\n--{drone.id}, b:{drone.battery:.2f} - P, t:{drone.timeToDoneCharging():.0f}"

        text = f"{text}\n Dead Drones:"
        for drone in self.world.drones:
            if drone.state == DroneState.TERMINATED:
                text = f"{text}\n-{drone.id}"
        
        totalDamage = sum([field.damage for field in self.world.fields])
        totalCorp = sum([field.allCrops for field in self.world.fields])
        text = f"{text}\n Damage: {totalDamage}/{totalCorp}"
        return text

    def drawLegends(self, draw):

        legendStartPoint = self.width - LEGEND_SIZE
        text = self.getLegends()
        draw.text((legendStartPoint + TEXT_MARGIN, TEXT_MARGIN), text, COLORS['text'])
        return draw

    def drawComponents(self, iteration=0):

        array = np.array(self.background, copy=True)

        for bird in self.world.birds:
            self.grid[bird] = self.drawRectangle(array, bird.location, 'bird')

        for drone in self.world.drones:
            self.grid[drone] = self.drawRectangle(array, drone.location, 'drone')

        for charger in self.world.chargers:
            self.grid[charger] = self.drawRectangle(array, charger.location, 'charger')

        for field in self.world.fields:
            for damagedCorp in field.damaged:
                self.drawRectangle(array, damagedCorp, 'corp')

        image = Image.fromarray(array.astype(np.uint8), 'RGB')
        draw = ImageDraw.Draw(image)
        for drone in self.world.drones:
            if drone.state == DroneState.TERMINATED:
                continue

            self.drawCircle(draw, drone.protectRadius())
            draw.text((self.grid[drone]), f"{drone.battery:.2f}\n{drone.id}", COLORS['text'])

        for charger in self.world.chargers:
            draw.text((self.grid[charger]), f"{charger.id}", COLORS['text'])

        draw = self.drawLegends(draw)
        self.images.append(image)

    def createAnimation(self, filename):
        self.images[0].save(filename, save_all=True, append_images=self.images[1:])
