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


class Replay_viewer:

    def __init__(self, env, num_humans, ai_policies,  show_planning, level, file, max_steps=100, render=False):
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

        #get the data for the replay
        f = open(file)
        self.data = json.load(f)
        self.timesteps = self.data['timestep']
        self.intentions_stacks = self.data['command_stacks']
        self.initial_intentions = self.data['initial_commands']
        self.player_actions = self.data['player_actions']
        self.ai_actions = self.data['ai_actions']
        self.commands_given = self.data['commands_given']
        self.actions_canceled = self.data['actions_canceled']


        self.clock = pygame.time.Clock()
        #max time for a game
        self.timer = 120
        #time passed
        self.time = 0
        self.next_action = 0

        self.recipes = self.env.unwrapped.recipes
        assert len(ai_policies) == len(env.unwrapped.world.agents) - num_humans
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def on_init(self):
        pygame.init()
        self.graphics_pipeline.on_init()
        self.graphics_pipeline.timer = self.timer
        pygame.display.set_caption("overcooked")
        self.next_action = self.timesteps.pop(0)
        intentions = []
        for intention in self.initial_intentions:
            intentions.append(Intention(intention))
        self.env.unwrapped.world.IntentionStack = intentions
        return True

    def on_event(self, event):
        self.step_done = False
        #update intentions
        self.graphics_pipeline.updateIntentions()
        human_action = None
        ai_action = None
        store_action_dict = {}
        if event == "Action":
            #human action is 0
            intentions = []
            for intention in self.intentions_stacks.pop(0):
                intentions.append(Intention(intention))
            self.env.unwrapped.world.IntentionStack = intentions

            commands_given = self.commands_given.pop(0)
            for command in commands_given:
                print("Player gave command: ", command)
            actions_canceled = self.actions_canceled.pop(0)
            for action in actions_canceled:
                print("Player canceled action: ", action)

            human_action = self.player_actions.pop(0)
            ai_action = self.ai_actions.pop(0)
            self.env.unwrapped.world.agents[0].action = human_action
            store_action_dict[self.env.unwrapped.world.agents[0]] = human_action
            self.store["observation"].append(self.last_obs)
            self.store["agent_states"].append([agent.location for agent in self.env.unwrapped.world.agents])

            # Here AI actions are performed
            agent = self.env.unwrapped.world.agents[1]
            store_action_dict[agent] = ai_action
            agent.action = ai_action
            self.step_done = True
        else:
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
        if self.step_done:
            self.resolve_action(human_action, ai_action, store_action_dict)


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
            if self.time > self.next_action:
                self.on_event("Action")
                if len(self.timesteps) > 0:
                    self.next_action = self.timesteps.pop(0)
            if(self.time > self.timer):
                self._running = False
                self.store["observation"].append(self.last_obs)
            self.on_render()
        #self.writeData()
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

    @staticmethod
    def on_cleanup():
        pygame.quit()

    def get_image_obs(self):
        return self.graphics_pipeline.get_image_obs()

    def save_image_obs(self, t):
        self.graphics_pipeline.save_image_obs(t)

    def resolve_action(self, human_action, ai_action, store_action_dict):
        self.yielding_action_dict = {agent: self.env.unwrapped.world_agent_mapping[agent].action
                                     for agent in self.env.agents}
        observations, rewards, dones, infos = self.env.step(self.yielding_action_dict)

        self.store["actions"].append(store_action_dict)
        self.store["info"].append(infos)
        self.store["rewards"].append(rewards)
        self.store["done"].append(dones)

        self.last_obs = observations

        if all(dones.values()):
            self._running = False
            self.store["observation"].append(self.last_obs)



