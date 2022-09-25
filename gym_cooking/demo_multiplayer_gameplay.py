from gym_cooking.environment.game.game_continous import Game_continous
from action_controller import ActionController
from gym_cooking.environment import cooking_zoo
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.utils.utils import ACTIONS_INTENTIONS_MAP
import action_mapping
import random

n_agents = 2
num_humans = 1
save_data = True
max_steps = 100
render = False
show_planning = True

level = 'exp1'
#level = 'exp2'
#level = 'exp3'
#level = 'open_room_blender'
#level = 'exp_test'
#level = 'exp_test2'
#level = 'exp_test3'
seed = 1
record = False
max_num_timesteps = 1000
recipes = ["TomatoLettuceOnionSalad", 'TomatoLettuceOnionSalad']
#recipes = ["TomatoLettuceSalad", 'TomatoLettuceSalad']

parallel_env = cooking_zoo.parallel_env(level=level, num_agents=n_agents, record=record,
                                        max_steps=max_num_timesteps, recipes=recipes, obs_spaces=["numeric"],allowed_objects=None,
                 max_rounds=0, respawn_at_same_locations=False) #oder numeric?

action_spaces = parallel_env.action_spaces
player_2_action_space = action_spaces["player_1"]


class CookingAgent:

    def __init__(self, action_space):
        self.action_space = action_space
        self.commandsToMovements = {'Skip':0,'Left':1,'Right':2,'Down':3,'Up':4,'F':5}
        self.commands = []

    def get_action(self, observation) -> int:
        if len(self.commands)>0:
            if(self.commands[0].intention in self.commandsToMovements.keys()):
                return self.commandsToMovements[self.commands.pop(0).intention]
        action = self.action_space.sample()
        return action

#todo fix rapid interactions spam fix basic level plotting
class RuleBasedCookingAgent:

    def __init__(self, action_space, agent_name): #name
        self.action_space = action_space
        self.controller = ActionController()
        self.action_mapping = action_mapping.ActionMapping()
        self.agent_name = agent_name
        self.commandsToMovements = {'Skip': 0, 'Left': 1, 'Right': 2, 'Down': 3, 'Up': 4, 'F': 5}
        #self.highLevelCommands = {'SliceTomato': action_mapping.Actions.CHOP_TOMATO, 'SliceLettuce': action_mapping.Actions.CHOP_LETTUCE, 'SliceOnion': action_mapping.Actions.CHOP_ONION}
        self.reversedHighLevelCommands = {v: k for k, v in action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP.items()}
        self.currentCommandLevel = 'High'
        self.commands = []
        self.highLevelRepresentation = []
        self.lowLevelRepresentation = []
        #give a penalty to an agent the number means the chance (in %) to idle when performing a certain high level task
        #self.penalties = [['SliceTomato'],[50]]
        self.penalties = [[],[]]

    def plan(self, observation, level):
        env_state = observation['symbolic_observation']
        agent_pos = observation['agent_location']
        if (self.currentCommandLevel == 'High'):
            self.highLevelRepresentation = self.commands.copy()
        #low level actions always plan the current high level action
        if(level == 'Basic'):
            #if no high level command is given, get a new high level action
            if len(self.highLevelRepresentation) == 0:
                currentHighLevelAction = self.controller.get_high_level_action(env_state, agent_pos)
            #if a command is given, convert it to an command and plan with it
            else:
                currentHighLevelAction = action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.highLevelRepresentation[0].intention]
            if currentHighLevelAction != action_mapping.Actions.DO_NOTHING:
                currentPlan = self.action_mapping.map_action(env_state, agent_pos, currentHighLevelAction, True)
                if currentPlan != 'nop':
                    if currentPlan == 'interact':
                        intention = Intention("F")
                        self.lowLevelRepresentation = [intention]
                    else:
                        self.lowLevelRepresentation = []
                        for action in currentPlan:
                            #toDo map actions to intentions
                            intention = Intention(ACTIONS_INTENTIONS_MAP[action])
                            self.lowLevelRepresentation.append(intention)
                #if the given high level action is do nothing, it is fullfilled, so get a new high level plan
                else:
                    self.highLevelRepresentation = []
                    self.plan(observation, 'High')
            else:
                self.lowLevelRepresentation = []
                self.lowLevelRepresentation.append(Intention("Skip"))
            self.changeCommandLevel(level)
        if(level == 'High'):
            if len(self.highLevelRepresentation) == 0:
                currentPlan = self.controller.get_high_level_action(env_state, agent_pos)
                if currentPlan != action_mapping.Actions.DO_NOTHING and currentPlan in self.reversedHighLevelCommands.keys():
                    intention = Intention(self.reversedHighLevelCommands[currentPlan])
                    self.highLevelRepresentation = [intention]
                    self.changeCommandLevel(level)

    def changeCommandLevel(self, commandLevel):
        if self.currentCommandLevel == 'High' and len(self.commands) != 0:
            self.highLevelRepresentation = self.commands.copy()
        self.currentCommandLevel = commandLevel
        self.commands.clear()
        if (commandLevel == 'Basic'):
            for intention in self.lowLevelRepresentation:
                self.commands.append(intention)
        if (commandLevel == 'High'):
            for intention in self.highLevelRepresentation:
                self.commands.append(intention)

    #ToDo pop actions in representations
    def get_action(self, observation) -> int:
        env_state = observation['symbolic_observation']
        agent_pos = observation['agent_location']
        self.controller.action_mapping.motion_generator.set_agent_position(agent_pos)
        #if no commands are given, the agent will show his current goal
        if len(self.commands) == 0:
            self.plan(observation, level = self.currentCommandLevel)
        if len(self.commands)>0:
            if(self.commands[0].intention in self.commandsToMovements.keys()):
                action = self.commandsToMovements[self.commands[0].intention]
                if len(self.highLevelRepresentation) > 0:
                    if (self.action_mapping.task_finished
                    (action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.highLevelRepresentation[0].intention],
                     action, env_state, agent_pos)):
                        return self.finish_goal(action)
                if self.check_for_penalty():
                    return 0
                return self.commandsToMovements[self.commands.pop(0).intention]
            if (self.commands[0].intention in action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP.keys()):
                #reset required for motion generator to work
                self.action_mapping.motion_generator.reset(env_state, agent_pos)
                action = self.action_mapping.map_action(env_state, agent_pos, action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.commands[0].intention], planning=False)
                if(self.action_mapping.task_finished
                    (action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.commands[0].intention],
                     action, env_state, agent_pos)):
                    return self.finish_goal(action)
                if self.check_for_penalty():
                    return 0
                return action
        #print("No plan; default Policy")
        return self.controller.get_low_level_action(env_state, agent_pos, planning=False)

    def check_for_penalty(self):
        if len(self.highLevelRepresentation) > 0:
            if self.highLevelRepresentation[0].intention in self.penalties[0]:
                if random.randint(0, 100) < self.penalties[1][self.penalties[0].index(self.highLevelRepresentation[0].intention)]:
                    #print("penalty")
                    return True
                else:
                    return False

    def finish_goal(self, action):
        if (action == 0):
            self.highLevelRepresentation = []
            self.commands.pop(0).intention
        if action == 5:
            if self.check_for_penalty():
                return 0
            self.highLevelRepresentation = []
            self.commands.pop(0).intention
            return action
        else:
            if self.check_for_penalty():
                return 0
            return action

cooking_agent = CookingAgent(player_2_action_space)
cooking_agent_rulebased = RuleBasedCookingAgent(player_2_action_space, "player_1")

#game = Game(parallel_env, num_humans, [cooking_agent_rulebased], playmode, show_planning, max_steps)
game = Game_continous(parallel_env, num_humans, [cooking_agent_rulebased], save_data, show_planning, level, 'replay', max_steps)
store = game.on_execute()
print("done")
