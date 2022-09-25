import os
from gym_cooking.environment.game import graphic_pipeline
from gym_cooking.misc.game.utils import *
from gym_cooking.cooking_world.world_objects import *

import pygame

import os.path
import json
from collections import defaultdict
from datetime import datetime
from time import sleep


os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'


class Game:

    def __init__(self, env, num_humans, ai_policies, playmode, show_planning, level, max_steps=100, render=False):
        self._running = True
        self.env = env
        self.play = bool(num_humans)
        self.play = True
        self.render = render or self.play
        # Visual parameters
        self.graphics_pipeline = graphic_pipeline.GraphicPipeline(env, self.render)
        self.graphics_pipeline.show_planning = show_planning
        self.save_dir = 'misc/game/screenshots'
        self.store = defaultdict(list)
        self.num_humans = num_humans
        self.ai_policies = ai_policies
        self.max_steps = max_steps
        self.current_step = 0
        self.last_obs = env.reset()
        self.step_done = False
        self.yielding_action_dict = {}
        self.level_name = level

        #data for saving replays, data is only written to file if playmode is True
        self.playmode = playmode
        self.player_actions = []
        self.ai_actions = []
        self.timestamps = []
        self.initial_command_stack = []
        self.command_stack = []
        self.command_levels = []
        self.tmp_commands_given = []
        self.commands_given = []
        self.tmp_actions_canceled = []
        self.actions_canceled = []

        self.clock = pygame.time.Clock()
        #max time for a game
        self.timer = 300
        #time passed
        self.time = 0

        self.recipes = self.env.unwrapped.recipes
        assert len(ai_policies) == len(env.unwrapped.world.agents) - num_humans
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def on_init(self):
        pygame.init()
        self.graphics_pipeline.on_init()
        self.graphics_pipeline.timer = self.timer
        pygame.display.set_caption("overcooked")
        self.changeCommandLevel("High")
        intentions = []
        for intention in self.env.unwrapped.world.IntentionStack:
            intentions.append(intention.intention)
        self.initial_command_stack = intentions
        if not self.playmode:
            agent = self.ai_policies[0]
            for command in agent.initial_commands:
                self.env.unwrapped.world.IntentionStack.append(Intention(command))
        return True

    def on_event(self, event):
        self.step_done = False
        #update intentions
        self.graphics_pipeline.updateIntentions()
        self.checkForButtonClicks(event)
        if event.type == pygame.QUIT:
            self._running = False
            self.store["observation"].append(self.last_obs)
        elif event.type == pygame.KEYDOWN:
            # exit the game
            if event.key == pygame.K_ESCAPE:
                self._running = False
                self.store["observation"].append(self.last_obs)
            # Save current image
            if event.key == pygame.K_RETURN:
                image_name = '{}_{}.png'.format(self.env.unwrapped.filename, datetime.now().strftime('%m-%d-%y_%H-%M-%S'))
                pygame.image.save(self.graphics_pipeline.screen, '{}/{}'.format(self.save_dir, image_name))
                print('Saved image {} to {}'.format(image_name, self.save_dir))
                return

            # Control current human agent
            if event.key in KeyToTuple_human1:
            #if event.key in KeyToTuple_human1 and self.num_humans > 0:
                if not self.playmode:
                    commands = self.ai_policies[0].intention_stack.pop(0)
                    intention_stack = []
                    for command in commands:
                        intention_stack.append(Intention(command))
                    self.env.unwrapped.world.IntentionStack = intention_stack
                    commands_given = self.ai_policies[0].commands_given.pop(0)
                    for command in commands_given:
                        print("Play gave command: ", command)
                    actions_canceled = self.ai_policies[0].actions_canceled.pop(0)
                    for action in actions_canceled:
                        print("Play canceled action: ", action)

                store_action_dict = {}
                action = KeyToTuple_human1[event.key]
                self.env.unwrapped.world.agents[0].action = action
                store_action_dict[self.env.unwrapped.world.agents[0]] = action
                self.store["observation"].append(self.last_obs)
                self.store["agent_states"].append([agent.location for agent in self.env.unwrapped.world.agents])
                for idx, agent in enumerate(self.env.unwrapped.world.agents):
                    if idx >= self.num_humans:
                        #add IntentionStackToAgent
                        self.ai_policies[idx - self.num_humans].commands = self.env.unwrapped.world.IntentionStack
                        ai_policy = self.ai_policies[idx - self.num_humans]
                        env_agent = self.env.unwrapped.world_agent_to_env_agent_mapping[agent]
                        last_obs_raw = self.last_obs[env_agent]
                        ai_action = ai_policy.get_action(last_obs_raw)
                        store_action_dict[agent] = ai_action
                        self.env.unwrapped.world.agents[idx].action = ai_action



                self.yielding_action_dict = {agent: self.env.unwrapped.world_agent_mapping[agent].action
                                             for agent in self.env.agents}
                observations, rewards, dones, infos = self.env.step(self.yielding_action_dict)



                self.store["actions"].append(store_action_dict)
                self.store["info"].append(infos)
                self.store["rewards"].append(rewards)
                self.store["done"].append(dones)

                self.last_obs = observations
                self.step_done = True

                #already plan the new step
                command_level = self.env.unwrapped.world.currentCommandLevel
                if self.playmode:
                    agent = self.ai_policies[0]
                    if len(agent.commands) == 0:
                        last_obs_raw = self.last_obs[self.env.unwrapped.world_agent_to_env_agent_mapping[self.env.unwrapped.world.agents[1]]]

                        agent.plan(last_obs_raw, command_level)
                newCommandStack = agent.commands
                self.env.unwrapped.world.IntentionStack = newCommandStack
                self.graphics_pipeline.IntentionStack = newCommandStack
                #self.changeCommandLevel(command_level)

                # store the actions for replay feature
                self.player_actions.append(action)
                self.ai_actions.append(ai_action)
                self.timestamps.append(self.time)
                intentions = []
                for intention in self.env.unwrapped.world.IntentionStack:
                    intentions.append(intention.intention)
                self.command_stack.append(intentions)
                self.command_levels.append(self.env.unwrapped.world.currentCommandLevel)
                self.commands_given.append(self.tmp_commands_given)
                self.actions_canceled.append(self.tmp_actions_canceled)
                self.tmp_commands_given = []
                self.tmp_actions_canceled = []

                if all(dones.values()):
                    self._running = False
                    self.store["observation"].append(self.last_obs)

    def ai_only_event(self):
        self.step_done = False

        store_action_dict = {}

        self.store["observation"].append(self.last_obs)
        self.store["agent_states"].append([agent.location for agent in self.env.unwrapped.world.agents])
        for idx, agent in enumerate(self.env.unwrapped.world.agents):
            if idx >= self.num_humans:
                ai_policy = self.ai_policies[idx - self.num_humans].agent
                env_agent = self.env.unwrapped.world_agent_to_env_agent_mapping[agent]
                last_obs_raw = self.last_obs[env_agent]
                ai_action = ai_policy.get_action(last_obs_raw)
                store_action_dict[agent] = ai_action
                self.env.unwrapped.world.agents[idx].action = ai_action

        self.yielding_action_dict = {agent: self.env.unwrapped.world_agent_mapping[agent].action
                                     for agent in self.env.agents}
        observations, rewards, dones, infos = self.env.step(self.yielding_action_dict)

        self.store["actions"].append(store_action_dict)
        self.store["info"].append(infos)
        self.store["rewards"].append(rewards)
        self.store["done"].append(dones)
        self.last_obs = observations
        self.step_done = True

        if all(dones.values()):
            self._running = False
            self.store["observation"].append(self.last_obs)

    def on_execute(self):
        self._running = self.on_init()
        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            dt = self.clock.tick() / 1000
            self.time += dt
            if(self.time > self.timer):
                self._running = False
                self.store["observation"].append(self.last_obs)
            self.on_render()
        self.writeData()
        self.on_cleanup()

        return self.store

    def on_execute_yielding(self):
        self._running = self.on_init()
        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_render()
            if self.step_done:
                self.step_done = False
                yield self.store["observation"][-1], self.store["done"][-1], self.store["info"][-1], \
                      self.store["rewards"][-1], self.yielding_action_dict
        self.writeData()
        self.on_cleanup()

    def on_execute_ai_only_with_delay(self):
        self._running = self.on_init()

        while self._running:
            sleep(0.2)
            self.ai_only_event()
            self.on_render()
        self.writeData()
        self.on_cleanup()

        return self.store

    def on_render(self):
        self.graphics_pipeline.time = self.time
        self.graphics_pipeline.on_render()

    def writeData(self):
        if self.playmode:
            data = {
                'level': self.level_name,
                'player_actions': self.player_actions,
                'ai_actions': self.ai_actions,
                'timestep': self.timestamps,
                'initial_commands': self.initial_command_stack,
                'command_stacks': self.command_stack,
                'current_command_level': self.command_levels,
                'commands_given': self.commands_given,
                'actions_canceled': self.actions_canceled

            }
            with open('replay.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)


    @staticmethod
    def on_cleanup():
        pygame.quit()

    def get_image_obs(self):
        return self.graphics_pipeline.get_image_obs()

    def save_image_obs(self, t):
        self.graphics_pipeline.save_image_obs(t)

    def changeCommandLevel(self, commandLevel):
        agent = self.ai_policies[0]
        if self.playmode:
            last_obs_raw = self.last_obs[self.env.unwrapped.world_agent_to_env_agent_mapping[self.env.unwrapped.world.agents[1]]]
            agent.plan(last_obs_raw, commandLevel)
            agent.changeCommandLevel(commandLevel)
            newCommandStack = agent.commands
            self.env.unwrapped.world.IntentionStack = newCommandStack
            self.graphics_pipeline.IntentionStack = newCommandStack

    def checkForButtonClicks(self, event,):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if (self.graphics_pipeline.isValidAgentButton(x,y)):
                button = self.graphics_pipeline.getButton(x, y)
                if self.playmode:
                    self.save_commands(button)
                self.env.unwrapped.world.resolveButtonClick(button)
                if button in self.env.unwrapped.world.commandLevels:
                    self.changeCommandLevel(button)
                self.ai_policies[0].commands = self.env.unwrapped.world.IntentionStack
                #print("test")

    def save_commands(self, button):
        #intention_stack popped
        if isinstance(button, int):
            self.tmp_actions_canceled.append(self.env.unwrapped.world.IntentionStack[button].intention)
        #command_level
        else:
            if button in self.env.unwrapped.world.commandLevels:
                pass
            #command_given
            else:
                self.tmp_commands_given.append(button)




