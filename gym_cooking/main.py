import pygame
from gym_cooking.environment.game.game_continous import Game_continous
from gym_cooking.environment import cooking_zoo
from cooking_agent import RuleBasedCookingAgent
from cooking_agent_updating import RuleBasedCookingAgentUpdating
from startscreen import Startscreen
from pausescreen import Pausescreen
from endscreen import Endscreen
from time import sleep
import signal
import random


n_agents = 2
num_humans = 1
max_steps = 100
render = False
show_planning = True
record = False
max_num_timesteps = 1000
recipes = ["TomatoLettuceOnionSalad", 'TomatoLettuceOnionSalad']

#save the replay files to the replay files folder
save_data = True

#run the 10 old levels
#levels = ['l1', 'l2','l3','l4','l5','l6','l7','l8','l9','l10']
#random.shuffle(levels)
#levels = ['l0'] + levels

levels = ['l1b', 'l2b','l3b','l4b','l5b','l6b','l7b','l8b','l9b','l10b','l11b', 'l12b','l13b','l14b','l15b','l16b','l17b','l18b','l19b','l20b']
random.shuffle(levels)
levels = ['l0b'] + levels

signal.signal(signal.SIGSEGV, signal.SIG_IGN)

#get name in startscreem
name = Startscreen().make_screen()
sleep(1)
pygame.display.quit()
for i in range(len(levels)):
    try:
        Pausescreen().make_screen()
        pygame.display.quit()
        sleep(1)
        print("Game ", i)
        parallel_env = cooking_zoo.parallel_env(level=levels[i], num_agents=n_agents, record=record,
                                                max_steps=max_num_timesteps, recipes=recipes, obs_spaces=["numeric"],
                                                allowed_objects=None,
                                                max_rounds=0, respawn_at_same_locations=False)
        #Updating plan at every high level action
        cooking_agent_rulebased = RuleBasedCookingAgent("player_1")
        #Updating plan at every step
        #cooking_agent_rulebased = RuleBasedCookingAgentUpdating("player_1")
        game = Game_continous(parallel_env, num_humans, [cooking_agent_rulebased], save_data, show_planning, levels[i], name + '_' + str(i), max_steps)  # name_1
        store = game.on_execute()
        pygame.display.quit()
        sleep(2)
    except Exception as e:
        print(levels[i], " crashed" , e)
        sleep(1)
Endscreen().make_screen()
pygame.quit()

