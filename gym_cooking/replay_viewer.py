from gym_cooking.environment.game.game import Game
from action_controller import ActionController
from gym_cooking.environment import cooking_zoo
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.utils.utils import ACTIONS_INTENTIONS_MAP
import action_mapping
import json

n_agents = 2
num_humans = 0
max_steps = 100
playmode = False
render = True

level = 'exp1'
replay_name = ('example_replay.json')

seed = 1
record = False
max_num_timesteps = 1000
recipes = ["TomatoLettuceOnionSalad", 'TomatoLettuceOnionSalad']
#recipes = ["TomatoLettuceSalad", 'TomatoLettuceSalad']

parallel_env = cooking_zoo.parallel_env(level=level, num_agents=n_agents, record=record,
                                        max_steps=max_num_timesteps, recipes=recipes, obs_spaces=["numeric"],allowed_objects=None,
                 max_rounds=0, respawn_at_same_locations=False) #oder numeric?




class replay_agent():
    def __init__(self, data, intention_stack, initial_intention, current_command_level, commands_given, actions_canceled):
        self.actions = data
        self.intention_stack = intention_stack
        self.initial_commands = initial_intention
        self.current_command_level = current_command_level
        self.commands_given = commands_given
        self.actions_canceled = actions_canceled

    def get_action(self, observation):
        action = self.actions.pop(0)
        return action

f = open(replay_name)
data = json.load(f)
agent1 = replay_agent(data['player_actions'], data['command_stacks'], data['initial_commands'],
                      data['current_command_level'], data['commands_given'], data['actions_canceled'])
agent2 = replay_agent(data['ai_actions'], data['command_stacks'], data['initial_commands'],
                      data['current_command_level'], data['commands_given'], data['actions_canceled'])

game = Game(parallel_env, num_humans, [agent1, agent2], playmode, True, level, max_steps)
store = game.on_execute()
print("done")
