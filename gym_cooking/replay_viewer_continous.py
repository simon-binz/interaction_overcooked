from gym_cooking.environment.game.replay_view import Replay_viewer
from action_controller import ActionController
from gym_cooking.environment import cooking_zoo
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.utils.utils import ACTIONS_INTENTIONS_MAP
import action_mapping
import json

#Enter Replay Name to watch here
replay_name = ('replays/AB_2.json')

n_agents = 2
num_humans = 1
max_steps = 100
show_planning = True
render = True
f = open(replay_name)
data = json.load(f)
level = data['level']

seed = 1
record = False
max_num_timesteps = 1000
recipes = ["TomatoLettuceOnionSalad", 'TomatoLettuceOnionSalad']

parallel_env = cooking_zoo.parallel_env(level=level, num_agents=n_agents, record=record,
                                        max_steps=max_num_timesteps, recipes=recipes, obs_spaces=["numeric"],allowed_objects=None,
                 max_rounds=0, respawn_at_same_locations=False) #oder numeric?




class replay_agent():
    def __init__(self):
        pass
    def get_action(self, observation):
        return 0
agent1 = replay_agent()

game = Replay_viewer(parallel_env, num_humans, [agent1], show_planning, level, replay_name, max_steps)
store = game.on_execute()
print("done")
