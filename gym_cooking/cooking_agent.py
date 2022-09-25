from action_controller import ActionController
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.utils.utils import ACTIONS_INTENTIONS_MAP
import action_mapping
import random

class RuleBasedCookingAgent:

    def __init__(self,  agent_name): #name
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

    #The agents plan can be seen as follows:
    #He has a current high level action: e.g.  "Cut Tomato" which is represented by an intention
    #This high level action is then planned with a set of low level actions given by a low level representation
    #in this setting the agent is only supposed to do high level planning

    def plan(self, observation, level):
        env_state = observation['symbolic_observation']
        agent_pos = observation['agent_location']
        self.highLevelRepresentation = self.commands.copy()
        if len(self.highLevelRepresentation) == 0:
            currentPlan = self.controller.get_high_level_action(env_state, agent_pos)
            if currentPlan != action_mapping.Actions.DO_NOTHING and currentPlan in self.reversedHighLevelCommands.keys():
                intention = Intention(self.reversedHighLevelCommands[currentPlan])
                self.highLevelRepresentation = [intention]
                self.changeCommandLevel(level)
            #else: #this results in the agent not looking for things he can do
            #    self.highLevelRepresentation = [Intention("DoNothing")]
            #    self.commands = self.highLevelRepresentation
        if len(self.lowLevelRepresentation) == 0 and len(self.highLevelRepresentation)>0:
            currentHighLevelAction = action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.highLevelRepresentation[0].intention]
            if currentHighLevelAction != action_mapping.Actions.DO_NOTHING:
                currentPlan = self.action_mapping.map_action(env_state, agent_pos, currentHighLevelAction, True)
                if currentPlan != 'nop':
                    if currentPlan == 'interact':
                        self.lowLevelRepresentation = [Intention("F")]
                    else:
                        self.lowLevelRepresentation = []
                        for action in currentPlan:
                            intention = Intention(ACTIONS_INTENTIONS_MAP[action])
                            self.lowLevelRepresentation.append(intention)
                #if the given high level action is do nothing, the low level intention is to do skip the turn
                else:
                    self.lowLevelRepresentation = [Intention("Skip")]
                    #self.highLevelRepresentation = []
                    #self.plan(observation, 'High')


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
        if len(self.commands) == 0 or len(self.lowLevelRepresentation) == 0:
            self.plan(observation, level = self.currentCommandLevel)
        if len(self.highLevelRepresentation)>0:
            if self.highLevelRepresentation[0].intention == "DoNothing":
                    return 0
            else:
                #might guard this statement
                action = self.commandsToMovements[self.lowLevelRepresentation.pop(0).intention]
                if (self.action_mapping.task_finished
                        (action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.highLevelRepresentation[0].intention],
                         action, env_state, agent_pos)):
                    return self.finish_goal(action)
                else:
                    return action
        return 0

#        if len(self.commands)>0:
#            if(self.commands[0].intention in self.commandsToMovements.keys()):
#                action = self.commandsToMovements[self.commands[0].intention]
#                if len(self.highLevelRepresentation) > 0:
#                    if (self.action_mapping.task_finished
#                    (action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.highLevelRepresentation[0].intention],
#                     action, env_state, agent_pos)):
#                        return self.finish_goal(action)
#                if self.check_for_penalty():
#                    return 0
#                return self.commandsToMovements[self.commands.pop(0).intention]
#            if (self.commands[0].intention in action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP.keys()):
#                #reset required for motion generator to work
#                self.action_mapping.motion_generator.reset(env_state, agent_pos)
#                action = self.action_mapping.map_action(env_state, agent_pos, action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.commands[0].intention], planning=False)
#                if(self.action_mapping.task_finished
#                    (action_mapping.INTENTIONS_HIGH_LEVEL_ACTIONS_MAP[self.commands[0].intention],
#                     action, env_state, agent_pos)):
#                    return self.finish_goal(action)
#                if self.check_for_penalty():
#                    return 0
#                return action
#        #print("No plan; default Policy")
#        return self.controller.get_low_level_action(env_state, agent_pos, planning=False)

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