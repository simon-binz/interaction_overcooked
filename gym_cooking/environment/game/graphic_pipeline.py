import pygame
#from gym_cooking.cooking_world.abstract_classes import *
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.misc.game.utils import *
from collections import defaultdict, namedtuple

import numpy as np
import pathlib
import os.path
import math


COLORS = ['blue', 'magenta', 'yellow', 'green']

_image_library = {}


def get_image(path):
    global _image_library
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path)
        _image_library[path] = image
    return image


GraphicsProperties = namedtuple("GraphicsProperties", ["pixel_per_tile", "holding_scale", "container_scale",
                                                       "width_pixel", "height_pixel", "tile_size", "holding_size",
                                                       "container_size", "holding_container_size"])


class GraphicPipeline:
    #Laptop
    #PIXEL_PER_TILE = 60
    # Desktop at home
    PIXEL_PER_TILE = 80
    #PIXEL_PER_TILE = 100
    #PIXEL_PER_TILE = 120
    HOLDING_SCALE = 0.5
    CONTAINER_SCALE = 0.7

    def __init__(self, env, display=False):
        pygame.init()
        self.env = env
        self.display = display
        self.screen = None
        self.graphics_dir = 'misc/game/graphics'
        self.graphics_properties = GraphicsProperties(self.PIXEL_PER_TILE, self.HOLDING_SCALE, self.CONTAINER_SCALE,
                                                      self.PIXEL_PER_TILE * self.env.unwrapped.world.width,
                                                      self.PIXEL_PER_TILE * self.env.unwrapped.world.height,
                                                      (self.PIXEL_PER_TILE, self.PIXEL_PER_TILE),
                                                      (self.PIXEL_PER_TILE * self.HOLDING_SCALE,
                                                       self.PIXEL_PER_TILE * self.HOLDING_SCALE),
                                                      (self.PIXEL_PER_TILE * self.CONTAINER_SCALE,
                                                       self.PIXEL_PER_TILE * self.CONTAINER_SCALE),
                                                      (self.PIXEL_PER_TILE * self.CONTAINER_SCALE * self.HOLDING_SCALE,
                                                       self.PIXEL_PER_TILE * self.CONTAINER_SCALE * self.HOLDING_SCALE))

        self.infoObject = pygame.display.Info()
        self.excess_width = (self.infoObject.current_w - (
                    self.graphics_properties.width_pixel + 4 * self.PIXEL_PER_TILE)) / 2
        self.excess_height = (self.infoObject.current_h - (
                    self.graphics_properties.height_pixel + 2 * self.PIXEL_PER_TILE)) / 2

        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = pathlib.Path(dir_name)
        self.root_dir = path.parent.parent

        #most command levels/intentions belong to the interaction-setting with multiple levels of abstractions

        #get state from world
        self.commandLevels = self.env.unwrapped.world.commandLevels
        self.currentCommandLevel = self.env.unwrapped.world.currentCommandLevel
        self.basic_intentions = self.env.unwrapped.world.basic_intentions
        self.high_level_intentions = self.env.unwrapped.world.high_level_intentions
        self.intentions2 = self.env.unwrapped.world.Intentions2
        self.IntentionStack = self.env.unwrapped.world.IntentionStack
        self.currentIntentionsButtons = []

        #show the agents plans
        self.show_planning = True


        #buttons for showing icons
        self.button1Agent = AgentButton((0, 1), 'agent-{}'.format(self.env.unwrapped.world.agents[0].color), Color.WHITE) #todo unused
        if (len(self.env.unwrapped.world.agents) > 1):
            self.button2Agent = AgentButton((0, 0), 'agent-{}'.format(self.env.unwrapped.world.agents[1].color), Color.WHITE)

        #buttons for commandLevels
        self.agent1_buttons = []
        for i in range(len(self.commandLevels)):
            self.agent1_buttons.append(IntentionButton((0, i+1), self.commandLevels[i], Color.WHITE))



        #basic command level
        #self.agent2_buttons_basic = []
        #if (len(self.env.unwrapped.world.agents) > 1):
        #    for i in range(6):
        #        self.agent2_buttons_basic.append(IntentionButton((self.env.unwrapped.world.width + 1, i + 1),
        #                                                   self.basic_intentions[i].intention, Color.WHITE))

        #high command level:
        self.agent2_buttons_high = []
        if (len(self.env.unwrapped.world.agents) > 1):
            for i in range(7):
                self.agent2_buttons_high.append(IntentionButton((self.env.unwrapped.world.width + 1, i + 1),
                                                               self.high_level_intentions[i].intention, Color.WHITE))
            for i in range(7):
                self.agent2_buttons_high.append(IntentionButton((self.env.unwrapped.world.width + 2, i + 1),
                                                               self.high_level_intentions[i + 7].intention,
                                                               Color.WHITE))
            for i in range(1):
                self.agent2_buttons_high.append(IntentionButton((self.env.unwrapped.world.width + 3, i + 1),
                                                               self.high_level_intentions[i + 14].intention,
                                                               Color.WHITE))

        #mid command level
        #self.agent2_buttons_high = []
        #if (len(self.env.unwrapped.world.agents) > 1):
        #    for i in range(7):
        #        self.agent2_buttons_high.append(IntentionButton((self.env.unwrapped.world.width + 1, i + 1),
        #                                                   self.intentions2.intentions[i+12].intention, Color.WHITE))



        self.agent2buttons = {#'Basic':self.agent2_buttons_basic,
                         #'Low':self.agent2_buttons_low,
                         'High':self.agent2_buttons_high,
                         #'High':self.agent2_buttons_high,
                         #'Highest':self.agent2_buttons_highest,
                         #'All':self.agent2_buttons_all}
                              }

        #each recipe gets mentioned twice
        self.recipes = self.env.unwrapped.recipes[::2]
        self.recipesToImage = {'TomatoLettuceOnionSalad':  "ChoppedLettuce-ChoppedOnion-ChoppedTomato"}


        #timer
        self.timer = 0
        self.time = 0

        #Draw the texts
        self.font = pygame.font.SysFont('timesnewroman',  30)
        self.goalsText = self.font.render('Goals:', True, Color.BLACK, Color.WHITE)
        self.goalsTextRect = self.goalsText.get_rect()
        self.goalsTextRect.center = (self.excess_width +self.PIXEL_PER_TILE//2, self.excess_height+ self.graphics_properties.width_pixel + 1*self.PIXEL_PER_TILE + self.PIXEL_PER_TILE // 2)

        self.commandsText = self.font.render('Commands:', True, Color.BLACK, Color.WHITE)
        self.commandsTextRect = self.commandsText.get_rect()
        self.commandsTextRect.center = (self.excess_width + self.graphics_properties.width_pixel + 2*self.PIXEL_PER_TILE + self.PIXEL_PER_TILE // 2, self.excess_height + self.PIXEL_PER_TILE // 2)
    def on_init(self):
        if self.display:
            #self.screen = pygame.display.set_mode((self.graphics_properties.width_pixel + 4* self.PIXEL_PER_TILE,
            #                                       self.graphics_properties.height_pixel + 2* self.PIXEL_PER_TILE))
            #semi fullscreen

            self.screen = pygame.display.set_mode((self.infoObject.current_w, self.infoObject.current_h))
            #set excess width and height
            self.excess_width = (self.infoObject.current_w - (self.graphics_properties.width_pixel + 4* self.PIXEL_PER_TILE))/2
            self.excess_height =  (self.infoObject.current_h -(self.graphics_properties.height_pixel + 2* self.PIXEL_PER_TILE))/2


        else:
            # Create a hidden surface
            self.screen = pygame.Surface((self.graphics_properties.width_pixel + 2* self.PIXEL_PER_TILE, self.graphics_properties.height_pixel))
        self.screen = self.screen
        return True

    def on_render(self):
        self.screen.fill(Color.FLOOR)

        self.draw_static_objects()

        self.draw_agents()

        self.draw_dynamic_objects()

        if(self.show_planning):
            self.draw_intentions()

        self.draw_goals()
        self.drawTimer()

        if self.display:
            pygame.display.flip()
            pygame.display.update()

    def draw_square(self):
        pass

    def draw_button(self, button: Button):
        #draw tiles
        sl = self.scaled_location(button.location)
        sl = (sl[0] + self.excess_width,  sl[1] + self.excess_height)
        fill = pygame.Rect(sl[0] , sl[1] , self.graphics_properties.pixel_per_tile,
                           self.graphics_properties.pixel_per_tile)
        pygame.draw.rect(self.screen, button.color, fill)

        #draw image
        image_path = f'{self.root_dir}/{self.graphics_dir}/{button.image}.png'
        image = pygame.transform.scale(get_image(image_path), self.graphics_properties.tile_size)
        self.screen.blit(image, sl)

    def draw_intentions(self):
        #draw agent Icons
        if (len(self.env.unwrapped.world.agents) > 1):
            self.draw_button(self.button2Agent)

        #draw command text
        self.screen.blit(self.commandsText, self.commandsTextRect)

        #draw command levels
        #for button in self.agent1_buttons:
        #    self.draw_button(button)
        if (len(self.env.unwrapped.world.agents) > 1):
            #draw commands
            self.currentButtons = self.agent2buttons[self.currentCommandLevel]
            for button in self.currentButtons:
                self.draw_button(button)

        #draw intention stack
        for i in range(len(self.currentIntentionsButtons)): #intenteion stack
            if(i < 7):
                #self.draw_button(IntentionButton((i + 1, 0), self.IntentionStack[i].intention, Color.WHITE)) #todo remove
                self.draw_button(self.currentIntentionsButtons[i])

#method for drawing te recipes at the bottom
    def draw_goals(self):
        # draw goals
        for i in range(len(self.recipes)):
            self.draw_button(IntentionButton((i + 1, 12), self.recipesToImage[self.recipes[i]], Color.WHITE))
        self.screen.blit(self.goalsText, self.goalsTextRect)

    def draw_static_objects(self):
        objects = self.env.unwrapped.world.get_object_list()
        static_objects = [obj for obj in objects if isinstance(obj, StaticObject)]
        for static_object in static_objects:
            self.draw_static_object(static_object)

    def draw_static_object(self, static_object: StaticObject):
        sl = self.scaled_location(static_object.location)
        fill = pygame.Rect(sl[0] + self.PIXEL_PER_TILE + self.excess_width, sl[1]+ self.PIXEL_PER_TILE + self.excess_height, self.graphics_properties.pixel_per_tile, #tst for buttons ToDO: rework
                           self.graphics_properties.pixel_per_tile)
        if isinstance(static_object, Counter):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
        elif isinstance(static_object, DeliverSquare):
            pygame.draw.rect(self.screen, Color.DELIVERY, fill)
            self.draw(static_object.file_name(), self.graphics_properties.tile_size, sl)
        elif isinstance(static_object, CutBoard):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
            self.draw(static_object.file_name(), self.graphics_properties.tile_size, sl)
        elif isinstance(static_object, Blender):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
            self.draw(static_object.file_name(), self.graphics_properties.tile_size, sl)
        elif isinstance(static_object, Floor): #not sure what this does
            pygame.draw.rect(self.screen, Color.FLOOR, fill)

    def draw_dynamic_objects(self):
        objects = self.env.unwrapped.world.get_object_list()
        dynamic_objects = [obj for obj in objects if isinstance(obj, DynamicObject)]
        dynamic_objects_grouped = defaultdict(list)
        for obj in dynamic_objects:
            dynamic_objects_grouped[obj.location].append(obj)
        for location, obj_list in dynamic_objects_grouped.items():
            if any([agent.location == location for agent in self.env.unwrapped.world.agents]):
                self.draw_dynamic_object_stack(obj_list, self.graphics_properties.holding_size,
                                               self.holding_location(location),
                                               self.graphics_properties.holding_container_size,
                                               self.holding_container_location(location))
            else:
                self.draw_dynamic_object_stack(obj_list, self.graphics_properties.tile_size,
                                               self.scaled_location(location),
                                               self.graphics_properties.container_size,
                                               self.container_location(location))

    def draw_dynamic_object_stack(self, dynamic_objects, base_size, base_location, holding_size, holding_location):
        highest_order_object = self.env.unwrapped.world.get_highest_order_object(dynamic_objects)
        if isinstance(highest_order_object, Container):
            self.draw(highest_order_object.file_name(), base_size, base_location)
            rest_stack = [obj for obj in dynamic_objects if obj != highest_order_object]
            if rest_stack:
                self.draw_food_stack(rest_stack, holding_size, holding_location)
        else:
            self.draw_food_stack(dynamic_objects, base_size, base_location)

    def draw_agents(self):
        for agent in self.env.unwrapped.world.agents:
            self.draw('agent-{}'.format(agent.color), self.graphics_properties.tile_size,
                      self.scaled_location(agent.location))
            if agent.orientation == 1:
                file_name = "arrow_left"
                location = self.scaled_location(agent.location)
                location = (location[0], location[1] + self.graphics_properties.tile_size[1] // 4)
                size = (self.graphics_properties.tile_size[0] // 4, self.graphics_properties.tile_size[1] // 4)
            elif agent.orientation == 2:
                file_name = "arrow_right"
                location = self.scaled_location(agent.location)
                location = (location[0] + 3 * self.graphics_properties.tile_size[0] // 4,
                            location[1] + self.graphics_properties.tile_size[1] // 4)
                size = (self.graphics_properties.tile_size[0] // 4, self.graphics_properties.tile_size[1] // 4)
            elif agent.orientation == 3:
                file_name = "arrow_down"
                location = self.scaled_location(agent.location)
                location = (location[0] + self.graphics_properties.tile_size[0] // 4,
                            location[1] + 3 * self.graphics_properties.tile_size[1] // 4)
                size = (self.graphics_properties.tile_size[0] // 4, self.graphics_properties.tile_size[1] // 4)
            elif agent.orientation == 4:
                file_name = "arrow_up"
                location = self.scaled_location(agent.location)
                location = (location[0] + self.graphics_properties.tile_size[0] // 4, location[1])
                size = (self.graphics_properties.tile_size[0] // 4, self.graphics_properties.tile_size[1] // 4)
            else:
                raise ValueError(f"Agent orientation invalid ({agent.orientation})")
            self.draw(file_name, size, location)

    def draw(self, path, size, location):
        image_path = f'{self.root_dir}/{self.graphics_dir}/{path}.png'
        image = pygame.transform.scale(get_image(image_path), (int(size[0]), int(size[1])))
        location = tuple((location[0] + self.PIXEL_PER_TILE+ self.excess_width, location[1] + self.PIXEL_PER_TILE + self.excess_height))  #moved for bar #ToDo: rework
        self.screen.blit(image, location)

    def draw_food_stack(self, dynamic_objects, base_size, base_loc):
        tiles = int(math.floor(math.sqrt(len(dynamic_objects) - 1)) + 1)
        size = (base_size[0] // tiles, base_size[1] // tiles)
        for idx, obj in enumerate(dynamic_objects):
            location = (base_loc[0] + size[0] * (idx % tiles), base_loc[1] + size[1] * (idx // tiles))
            self.draw(obj.file_name(), size, location)

    def scaled_location(self, loc):
        """Return top-left corner of scaled location given coordinates loc, e.g. (3, 4)"""
        return tuple(self.graphics_properties.pixel_per_tile * np.asarray(loc))

    def holding_location(self, loc):
        """Return top-left corner of location where agent holding will be drawn (bottom right corner)
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        return tuple((np.asarray(scaled_loc) + self.graphics_properties.pixel_per_tile *
                      (1 - self.HOLDING_SCALE)).astype(int))

    def container_location(self, loc):
        """Return top-left corner of location where contained (i.e. plated) object will be drawn,
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        return tuple((np.asarray(scaled_loc) + self.graphics_properties.pixel_per_tile *
                      (1 - self.CONTAINER_SCALE) / 2).astype(int))
    
    def holding_container_location(self, loc):
        """Return top-left corner of location where contained, held object will be drawn
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        factor = (1 - self.HOLDING_SCALE) + (1 - self.CONTAINER_SCALE) / 2 * self.HOLDING_SCALE
        return tuple((np.asarray(scaled_loc) + self.graphics_properties.pixel_per_tile * factor).astype(int))

    def get_image_obs(self):
        self.on_render()
        img_int = pygame.PixelArray(self.screen)
        img_rgb = np.zeros([img_int.shape[1], img_int.shape[0], 3], dtype=np.uint8)
        for i in range(img_int.shape[0]):
            for j in range(img_int.shape[1]):
                color = pygame.Color(img_int[i][j])
                img_rgb[j, i, 0] = color.g
                img_rgb[j, i, 1] = color.b
                img_rgb[j, i, 2] = color.r
        return img_rgb

    def save_image_obs(self, t):
        game_record_dir = 'misc/game/record/example/'
        self.on_render()
        pygame.image.save(self.screen, '{}/t={:03d}.png'.format(game_record_dir, t))

    #method for displaying the plan of the agent
    def updateIntentions(self):
        self.currentCommandLevel = self.env.unwrapped.world.currentCommandLevel
        self.intentions2 = self.env.unwrapped.world.Intentions2
        self.IntentionStack = self.env.unwrapped.world.IntentionStack
        tmp = []
        for i in range (len(self.IntentionStack)):
            tmp.append(IntentionButton((i + 1, 0), self.IntentionStack[i].intention, Color.WHITE))
        self.currentIntentionsButtons = tmp


    def isValidAgentButton(self, x, y):
        #descale x and y
        if(self.show_planning == False):
            return False
        dx = (x - self.excess_width) / self.graphics_properties.pixel_per_tile
        dy = (y - self.excess_height) / self.graphics_properties.pixel_per_tile
        for button in (self.agent1_buttons + self.agent2buttons[self.currentCommandLevel] + self.currentIntentionsButtons):
            x = button.location[0]
            y = button.location[1]
            if (x<dx<x+1 and y<dy<y+1):
                return True
        return False

#return the button of the given location
    def getButton(self, x, y):
        #descale x and y
        dx = (x-self.excess_width) / self.graphics_properties.pixel_per_tile
        dy = (y-self.excess_height) / self.graphics_properties.pixel_per_tile
        for button in (self.agent1_buttons + self.agent2buttons[self.currentCommandLevel]): #self.agent1_buttons +
            x = button.location[0]
            y = button.location[1]
            if (x<dx<x+1 and y<dy<y+1):
                return button.image
        for i in range (len(self.currentIntentionsButtons)):
            button = (self.currentIntentionsButtons[i])
            x = button.location[0]
            y = button.location[1]
            if (x < dx < x + 1 and y < dy < y + 1):
                return i

    def drawTimer(self):
        timeLeftText = self.font.render('Time left:', True, Color.BLACK, Color.WHITE)
        timeLeftTextRect = timeLeftText.get_rect()
        timeLeftTextRect.center = (self.excess_width + self.graphics_properties.width_pixel + 2 * self.PIXEL_PER_TILE, self.excess_height + self.graphics_properties.width_pixel + 1 * self.PIXEL_PER_TILE+ self.PIXEL_PER_TILE/2)
        timeText = self.font.render(str(self.timer - round(self.time)) + "s", True, Color.BLACK, Color.WHITE)
        timeTextRect = timeText.get_rect()
        timeTextRect.center = (self.excess_width + self.graphics_properties.width_pixel + 3 * self.PIXEL_PER_TILE + self.PIXEL_PER_TILE/2, self.excess_height +  self.graphics_properties.width_pixel + 1 * self.PIXEL_PER_TILE+ self.PIXEL_PER_TILE/2)
        self.screen.blit(timeLeftText, timeLeftTextRect)
        self.screen.blit(timeText, timeTextRect)






