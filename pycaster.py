from math import sqrt, atan2, radians, degrees, sin, cos, tan, atan, acos
import pygame
from random import randint

SIZE = (800,800)
screen = 0

def random_colour():
    return (randint(0, 255), randint(0, 255), randint(0, 255))

def convert_angle(theta):
    absolute = theta%360
    if absolute >= 180 and absolute < 360:
        return absolute-360
    return absolute

def convertAngle(theta, fov):
    ntheta = 0
    onScreen = True
    if degrees(theta) < 0:                                          # If the angle is less than 0, rotate it
        theta += radians(360)
    if theta >= radians(270):                                       # If it is greater than 270 degrees, Subtract 360
        ntheta = theta-radians(360)                                 # to get in range from -90 to 0 
    elif theta >= radians(180) and theta < radians(270):            # If it is between 180 and 270
        ntheta = radians(-90)+radians(270)-theta                    # get it between -90 and 0 and aswell
        onScreen = False                                            # must be off screen for this to be necessary
    elif theta >= radians(90) and theta < radians(180):             # If it is between 90 and 180
        ntheta = radians(180)-theta                                 # get it between 0 and 90
        onScreen = False                                            # must be off screen for this to be necessary
    else:
        ntheta = theta                                              # else it is fine and on screen
    if (degrees(ntheta) < -fov/2 or degrees(ntheta) > fov/2):       # if outside the field of view, it is offscreen
        onScreen = False
    return ntheta, onScreen

def initScreen():
    global SIZE, screen
    pygame.init()
    screen = pygame.display.set_mode(SIZE)

class Camera:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.angle = -90
        self.fov = 90
        self.vfov = 135
        self.view_distance = 300

class Object:
    def __init__(self, x, y, h):
        self.x = x
        self.y = y
        self.height = h
        self.render_x = 0
        self.l_render_x = 0
        self.render_y = 0
        self.on_screen = False
        self.l_angle = 0
        self.collision = False
        self.cam_distance = 0
        # self.render_size = 0
    def updateRenderPosition(self, c: Camera):                                                          # References to object refer to a single vertex not the whole object
        player_object_angle = atan2(self.y-c.y, self.x-c.x)                                             # Get angle between line intersecting camera parallel to x axis, and the object
        c.angle = c.angle%360                                                                           # Convert the player view direction to be between 0 and 359 degrees
        angle = (radians(convert_angle(c.angle))) - (radians(degrees(player_object_angle)))             # Get the angle between the player view direction and the camera-object angle (but first convert them to be between -180 and 180)
        self.on_screen = True
        angle, self.on_screen = convertAngle(angle, c.fov)                                              # Convert that angle to be between -90 and 90 (as whether the object is ahead of or behind camera is irrelevant), and in the process flag whether the object is on screen
        self.cam_distance = sqrt((self.x-c.x)**2+(self.y-c.y)**2)                                       # Calculate the distance between the camera and point/object
        screenWidth = (tan(radians(c.fov/2))*self.cam_distance)                                         # Half (necessary in calculations) the field of view width at the depth of the object is equal to tan(fieldOfView/2)*depth
        objectScreenWidth = -tan(angle)*self.cam_distance                                               # How far (laterally) from the center of the screen the point is is defined as -tan(player-view-object-angle)*depth
        self.render_x = (SIZE[0]/2)+(objectScreenWidth/screenWidth)*SIZE[0]                             # Thus you can calculate this distance as a fraction of the lateral field of view width and multiply it by the screenWidth (size[0]) and add it to half the screenwidth to centre it.
        dValue = self.cam_distance*cos(abs(angle))                                                      # This is to remove the fish eye effect, ie to get a flat field of view rather than curved.
        self.render_y = (SIZE[1]/2)-(self.height/(dValue*tan(radians(c.vfov/2))))*(SIZE[1]/2)           # Similar to calculating the render x projection, this time taking the object height and dividing it by the field of view height at the object depth.
    
class Polygon:
    def __init__(self, points, colour):
        self.points = points
        self.colour = colour
        self.onScreen = False
        self.averageDistance = 0
    def testCollision(self, c: Camera, error_threshold):
        xBoundary = []
        yBoundary = []
        for pointCount in range(0, len(self.points)):
            xBoundary.append(self.points[pointCount].x)
            yBoundary.append(self.points[pointCount].y)
        xBoundary.sort()
        yBoundary.sort()
        if (c.x > xBoundary[0]-error_threshold and c.x < xBoundary[2]+error_threshold and c.y > yBoundary[0]-error_threshold and c.y < yBoundary[2]+error_threshold):
            return True
        return False
    def update(self, c: Camera):
        for i in range(0, len(self.points)):
            self.points[i].updateRenderPosition(c)
            self.averageDistance += self.points[i].cam_distance
        self.averageDistance /= len(self.points)
    def render(self, screen):
        onScreenCount = 0
        self.onScreen = True
        for point in self.points:
            if point.on_screen == False:
                onScreenCount += 1
        if onScreenCount == len(self.points):
            self.onScreen = False
        if self.onScreen:
            pygame.draw.polygon(screen, self.colour, [(int(self.points[0].render_x), int(self.points[0].render_y)), (int(self.points[1].render_x), int(self.points[1].render_y)), (int(self.points[2].render_x), int(self.points[2].render_y)), (int(self.points[3].render_x), int(self.points[3].render_y))])

class GameObjects:
    def __init__(self, polygons):
        self.polygons = polygons
        self.renderOrder = []
        self.skyColour = [135, 206, 235]
        self.floorColour = [126, 200, 80]
    def setBackgroundColours(self, s, f):
        self.skyColour = s
        self.floorColour = f
    def update(self, c):
        for i in range(0, len(self.polygons)):
            self.polygons[i].update(c)
    def render(self, screen):
        pygame.draw.polygon(screen, self.skyColour, ((0, 0), (SIZE[0], 0), (SIZE[0], SIZE[1]/2), (0, SIZE[1]/2)))
        pygame.draw.polygon(screen, self.floorColour, ((0, SIZE[1]/2), (SIZE[0], SIZE[1]/2), (SIZE[0], SIZE[1]), (0, SIZE[1])))
        self.renderOrder = [p for p in self.polygons]
        self.renderOrder.sort(key=lambda d: d.averageDistance)
        self.renderOrder = self.renderOrder[::-1]
        for polygon in self.renderOrder:
            polygon.render(screen)
    def testCollisions(self, c):
        for polygon in self.polygons:
            if polygon.testCollision(c, .4):
                return True
        return False


def getKeyPresses(keyPresses):
    quit = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                keyPresses.append("right")
            if event.key == pygame.K_LEFT:
                keyPresses.append("left")
            if event.key == pygame.K_a:
                keyPresses.append("a")
            if event.key == pygame.K_d:
                keyPresses.append("d")
            if event.key == pygame.K_w:
                keyPresses.append("w")
            if event.key == pygame.K_s:
                keyPresses.append("s")
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT:
                del keyPresses[keyPresses.index("right")]
            if event.key == pygame.K_LEFT:
                del keyPresses[keyPresses.index("left")]
            if event.key == pygame.K_a:
                del keyPresses[keyPresses.index("a")]
            if event.key == pygame.K_d:
                del keyPresses[keyPresses.index("d")]
            if event.key == pygame.K_w:
                del keyPresses[keyPresses.index("w")]
            if event.key == pygame.K_s:
                del keyPresses[keyPresses.index("s")]
    return keyPresses, quit

clock = pygame.time.Clock()

def screenClear():
    screen.fill((255, 255, 255))

def screenUpdate():
    pygame.display.flip()