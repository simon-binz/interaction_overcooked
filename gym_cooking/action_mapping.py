from enum import IntEnum, Enum
import numpy as np
#import torch

from gym_cooking.utils.utils import ACTION_MAP, MAP_OBJECT_TO_NUMBER, MAP_NUMBER_TO_OBJECT
from motion_generator import MotionGenerator


# Reduced high level action set for learning
class Actions(IntEnum):
    CHOP_LETTUCE = 0
    CHOP_TOMATO = 1
    CHOP_ONION = 2

    TOMATO_PLATE = 3
    LETTUCE_PLATE = 4
    ONION_PLATE = 5
    TOMATO_LETTUCE_PLATE = 6
    TOMATO_ONION_PLATE = 7
    LETTUCE_ONION_PLATE = 8
    TOMATO_LETTUCE_ONION_PLATE = 10

    GIVE_TOMATO = 11
    GIVE_LETTUCE = 12
    GIVE_ONION = 13
    GIVE_CHOPPED_TOMATO = 14
    GIVE_CHOPPED_LETTUCE = 15
    GIVE_CHOPPED_ONION = 16
    GIVE_PLATE = 17

    DELIVER = 18

    DO_NOTHING = 19


class ActionTypes(Enum):
    PROCESS = {Actions.CHOP_LETTUCE, Actions.CHOP_TOMATO, Actions.CHOP_ONION}

    PLATE = {Actions.TOMATO_PLATE, Actions.LETTUCE_PLATE, Actions.ONION_PLATE, Actions.TOMATO_LETTUCE_PLATE,
             Actions.TOMATO_ONION_PLATE, Actions.LETTUCE_ONION_PLATE, Actions.TOMATO_LETTUCE_ONION_PLATE}

    DELIVER = {Actions.DELIVER}

    #Maybe GIVE needs to be appended
    GIVE = {Actions.GIVE_TOMATO, Actions.GIVE_LETTUCE, Actions.GIVE_ONION,
            Actions.GIVE_CHOPPED_TOMATO, Actions.GIVE_CHOPPED_LETTUCE, Actions.GIVE_CHOPPED_ONION,
            Actions.GIVE_PLATE}


PROCESS_ACTIONS = {
    Actions.CHOP_LETTUCE: 'ChoppedTomato', #ToDo: warum steht hier ChoppedTomato?
    Actions.CHOP_TOMATO: 'ChoppedTomato', #
    Actions.CHOP_ONION: 'ChoppedTomato', #, 'ChoppedTomato
}

MAP_ACTIONS_TO_OBJECTS = {
    # needed tool, object, processed object
    Actions.CHOP_LETTUCE: ['CutBoard', 'Lettuce', 'ChoppedLettuce'],
    Actions.CHOP_TOMATO: ['CutBoard', 'Tomato', 'ChoppedTomato'],
    Actions.CHOP_ONION: ['CutBoard', 'Onion', 'ChoppedOnion'],

    # plate, ingredients
    Actions.TOMATO_PLATE: ['Plate', 'ChoppedTomato'],
    Actions.LETTUCE_PLATE: ['Plate', 'ChoppedLettuce'],
    Actions.ONION_PLATE: ['Plate', 'ChoppedOnion'],
    Actions.TOMATO_LETTUCE_PLATE: ['Plate', 'ChoppedTomato', 'ChoppedLettuce'],
    Actions.TOMATO_ONION_PLATE: ['Plate', 'ChoppedTomato', 'ChoppedOnion'],
    Actions.LETTUCE_ONION_PLATE: ['Plate', 'ChoppedLettuce', 'ChoppedOnion'],
    Actions.TOMATO_LETTUCE_ONION_PLATE: ['Plate', 'ChoppedTomato', 'ChoppedLettuce', 'ChoppedOnion'],

    # deliverSquare, plate
    Actions.DELIVER: ['DeliverSquare', 'Plate'],

    # counter, item to give
    Actions.GIVE_TOMATO: ['Counter', 'Tomato'],
    Actions.GIVE_LETTUCE: ['Counter', 'Lettuce'],
    Actions.GIVE_ONION: ['Counter', 'Onion'],
    Actions.GIVE_CHOPPED_TOMATO: ['Counter', 'ChoppedTomato'],
    Actions.GIVE_CHOPPED_LETTUCE: ['Counter', 'ChoppedLettuce'],
    Actions.GIVE_CHOPPED_ONION: ['Counter', 'ChoppedOnion'],
    Actions.GIVE_PLATE: ['Counter', 'Plate'],

    Actions.DO_NOTHING: []
}

HIGH_LEVEL_ACTIONS_INTENTIONS_MAP = {
    Actions.CHOP_TOMATO:'FreshTomato',
    Actions.CHOP_LETTUCE: 'FreshLettuce',
    Actions.CHOP_ONION: 'FreshOnion'
}

INTENTIONS_HIGH_LEVEL_ACTIONS_MAP = {
    'SliceTomato': Actions.CHOP_TOMATO,
    'SliceLettuce': Actions.CHOP_LETTUCE,
    'SliceOnion': Actions.CHOP_ONION,

    'GiveTomato' :Actions.GIVE_TOMATO,
    'GiveLettuce' :Actions.GIVE_LETTUCE,
    'GiveOnion' : Actions.GIVE_ONION,
    'GivePlate' : Actions.GIVE_PLATE,
    'GiveChoppedTomato' : Actions.GIVE_CHOPPED_TOMATO,
    'GiveChoppedLettuce': Actions.GIVE_CHOPPED_LETTUCE,
    'GiveChoppedOnion': Actions.GIVE_CHOPPED_ONION,

    'ChoppedTomatoPlate': Actions.TOMATO_PLATE,
    'ChoppedLettucePlate': Actions.LETTUCE_PLATE,
    'ChoppedOnionPlate': Actions.ONION_PLATE,
    'ChoppedLettuceTomatoPlate': Actions.TOMATO_LETTUCE_PLATE,
    'ChoppedOnionTomatoPlate': Actions.TOMATO_ONION_PLATE,
    'ChoppedLettuceOnionPlate': Actions.LETTUCE_ONION_PLATE,
    'ChoppedLettuceOnionTomatoPlate': Actions.TOMATO_LETTUCE_ONION_PLATE,
    'DoNothing': Actions.DO_NOTHING,

    'delivery': Actions.DELIVER
}


class ActionMapping:

    def __init__(self):
        self.motion_generator = MotionGenerator()

    def map_action(self, env_state, agent_pos, high_level_action, planning):
        """ returns a low level action """

        self.motion_generator.agent_position = agent_pos
        self.motion_generator.set_environment_state(environment_state= env_state)
        # all actions that process the ingredients
        if high_level_action in ActionTypes.PROCESS.value:
            objects = MAP_ACTIONS_TO_OBJECTS[high_level_action]

            interaction_object_plane = env_state[:, :, MAP_OBJECT_TO_NUMBER[objects[0]]]
            object_plane_index = MAP_OBJECT_TO_NUMBER[objects[1]]
            object_plane = env_state[:, :, object_plane_index]
            processed_object_plane = env_state[:, :, MAP_OBJECT_TO_NUMBER[objects[2]]]

            # if agent is holding something, check if he is holding the desired object
            if self._check_multiple_objects_at_position(env_state, agent_pos):
                held_object = self._get_object_held_by_agent(env_state, agent_pos)
                if held_object != objects[1]:
                    interaction_object_plane = self._get_free_counters(env_state)

            # if task is not already fulfilled
            if not self.check_objects_at_same_position(processed_object_plane, interaction_object_plane):
                if planning:
                    return self.plan_next_actions(env_state, agent_pos, object_plane_index, interaction_object_plane)
                return self._get_next_action(env_state, agent_pos, object_plane_index, interaction_object_plane)

            else:
                if planning:
                    return 'nop'
                return ACTION_MAP['nop']

        # all actions that put ingredients on a plate
        elif high_level_action in ActionTypes.PLATE.value:
            # print('PLATE')
            # feature planes
            objects = MAP_ACTIONS_TO_OBJECTS[high_level_action]
            interaction_plane = env_state[:, :, MAP_OBJECT_TO_NUMBER[objects[0]]]

            # if agent is holding a plate or a object that is not needed, let him place it on a free counter
            if self._check_multiple_objects_at_position(env_state, agent_pos):
                held_object = self._get_object_held_by_agent(env_state, agent_pos)
                if held_object == 'Plate' or held_object not in objects:
                    interaction_plane = self._get_free_counters(env_state)

            for i in range(1, len(objects)):
                object_plane_index = MAP_OBJECT_TO_NUMBER[objects[1]]
                object_plane = env_state[:, :, object_plane_index]
                if not self.check_objects_at_same_position(object_plane, interaction_plane):
                    if planning:
                        return self.plan_next_actions(env_state, agent_pos, object_plane_index, interaction_plane)
                    return self._get_next_action(env_state, agent_pos, object_plane_index, interaction_plane)
            if planning:
                return 'nop'
            return ACTION_MAP['nop']

        # all actions that deliver the plate
        elif high_level_action in ActionTypes.DELIVER.value:
            objects = MAP_ACTIONS_TO_OBJECTS[high_level_action]
            interaction_object_plane = env_state[:, :, MAP_OBJECT_TO_NUMBER[objects[0]]]
            object_plane_index = MAP_OBJECT_TO_NUMBER[objects[1]]
            object_plane = env_state[:, :, object_plane_index]

            # if agent is holding something, check if he is holding the desired object
            if self._check_multiple_objects_at_position(env_state, agent_pos):
                held_object = self._get_object_held_by_agent(env_state, agent_pos)
                if held_object != objects[1]:
                    interaction_object_plane = self._get_free_counters(env_state)
            if planning:
                return self.plan_next_actions(env_state, agent_pos, object_plane_index, interaction_object_plane)
            return self._get_next_action(env_state, agent_pos, object_plane_index, interaction_object_plane)
        elif high_level_action in ActionTypes.GIVE.value:
            objects = MAP_ACTIONS_TO_OBJECTS[high_level_action]
            object_plane_index = MAP_OBJECT_TO_NUMBER[objects[1]]
            mutually_available_counters = self._get_mutual_available_counters(env_state)

            # reduce to only free counters
            mutually_available_free_counters = []
            for c in mutually_available_counters:
                if np.sum(env_state[c]) == 1:
                    mutually_available_free_counters.append(c)

            mutually_available_free_counter_plane = self._create_plane_from_positions(mutually_available_free_counters,
                                                                                      np.shape(env_state[:, :, 0]))
            if planning:
                return self.plan_next_actions(env_state, agent_pos, object_plane_index, mutually_available_free_counter_plane)
            return self._get_next_action(env_state, agent_pos, object_plane_index,
                                         mutually_available_free_counter_plane)
        elif high_level_action == Actions.DO_NOTHING:
            if planning:
                return 'nop'
            return ACTION_MAP['nop']
        else:
            if planning:
                return 'nop'
            return ACTION_MAP['nop']

    def _get_next_action(self, env_state, agent_pos, object_plane_index, interaction_object_plane):
        object_plane = env_state[:, :, object_plane_index]
        if not self.check_object_is_reachable(env_state, object_plane_index, agent_pos):
            return ACTION_MAP['nop']

        # if the object is in the level
        goal_positions = self._get_object_positions(object_plane)
        # if agent already holds the object
        agent_holding_object = False
        agent_holding_target = False
        if self._check_multiple_objects_at_position(env_state, agent_pos):
            # find the position of the interaction object
            # TODO utilize to get agent to drop object before switching goal
            agent_holding_object = True
            if self._check_agent_at_goal_position(tuple(agent_pos), self._get_object_positions(object_plane)):
                agent_holding_target = True
            goal_positions = self._get_object_positions(interaction_object_plane)


            object_plane_index = MAP_OBJECT_TO_NUMBER["CutBoard"]
            object_plane = env_state[:, :, object_plane_index]
            cutboard_positions = self._get_object_positions(object_plane)
            rmv = []
            for i in range(len(goal_positions)):
                if goal_positions[i] in cutboard_positions:
                    if self._check_multiple_objects_at_position(env_state, goal_positions[i]):
                        rmv = [i] + rmv
            for item in rmv:
                goal_positions.pop(item)




        # generate a path
        shortest_path = (None, ['nop'])
        shortest_path_len = np.inf
        for goal in goal_positions:
            self.motion_generator.reset(env_state, tuple(agent_pos))
            path = self.motion_generator.shortest_path(tuple(agent_pos), goal)


            # path is not (None, 'nop')
            if path[0] is not None:
                new_path_length = len(path[1])
                if new_path_length < shortest_path_len:
                    shortest_path = path
                    shortest_path_len = new_path_length

            else:
                # if agent is directly next to goal
                if self._check_fields_next_to_each_other(goal, agent_pos):
                    return ACTION_MAP['interact']

        # return the first action in the path
        return ACTION_MAP[shortest_path[1][0]]

    def plan_next_actions(self, env_state, agent_pos, object_plane_index, interaction_object_plane):
        object_plane = env_state[:, :, object_plane_index]
        if not self.check_object_is_reachable(env_state, object_plane_index, agent_pos):
            return 'nop'

        # if the object is in the level
        goal_positions = self._get_object_positions(object_plane)

        # if agent already holds the object
        agent_holding_object = False
        agent_holding_target = False
        if self._check_multiple_objects_at_position(env_state, agent_pos):
            # find the position of the interaction object
            # TODO utilize to get agent to drop object before switching goal
            agent_holding_object = True
            if self._check_agent_at_goal_position(tuple(agent_pos), self._get_object_positions(object_plane)):
                agent_holding_target = True
            goal_positions = self._get_object_positions(interaction_object_plane)

            #remove occupied cutboards
            object_plane_index = MAP_OBJECT_TO_NUMBER["CutBoard"]
            object_plane = env_state[:, :, object_plane_index]
            cutboard_positions = self._get_object_positions(object_plane)
            rmv = []
            for i in range(len(goal_positions)):
                if goal_positions[i] in cutboard_positions:
                    if self._check_multiple_objects_at_position(env_state, goal_positions[i]):
                        rmv = [i] + rmv
            for item in rmv:
                goal_positions.pop(item)


        # generate a path
        shortest_path = (None, ['nop'])
        shortest_path_len = np.inf
        for goal in goal_positions:
            self.motion_generator.reset(env_state, tuple(agent_pos))
            path = self.motion_generator.shortest_path(tuple(agent_pos), goal)

            # path is not (None, 'nop')
            if path[0] is not None:
                new_path_length = len(path[1])
                if new_path_length < shortest_path_len:
                    shortest_path = path
                    shortest_path_len = new_path_length

            else:
                # if agent is directly next to goal
                if self._check_fields_next_to_each_other(goal, agent_pos):
                    return 'interact'

        # return the first action in the path
        return shortest_path[1]

    @staticmethod
    def check_objects_at_same_position(object_plane, interaction_object_plane):
        """
        checks if a given object is placed on the interaction object
        TODO: how to deal with multiple plates and multiple of the same objects?
        :param object_plane: object feature plane
        :param interaction_object_plane: interaction object feature plane
        :return: True if object is on the same position as the interaction object
        """
        plane1 = np.equal(object_plane, np.ones_like(object_plane))
        plane2 = np.equal(interaction_object_plane, np.ones_like(interaction_object_plane))
        comb = np.logical_and(plane1, plane2)
        return np.sum(comb) > 0

    @staticmethod
    def _check_multiple_objects_at_position(env_state, position):
        """Returns true if there are multiple objects at the given position, e.g. an agent holding something. False otherwise."""
        return np.sum(env_state[tuple(position)][2:16]) > 1

    def _get_object_held_by_agent(self, env_state, agent_position):
        """Returns a string describing the object held by the agent at the given position. None otherwise."""
        if not self._check_multiple_objects_at_position(env_state, agent_position):
            return None
        else:
            objects_held = []
            for i in range(4, 15):
                if env_state[tuple(agent_position)][i] == 1:
                    objects_held.append(MAP_NUMBER_TO_OBJECT[i])
            return 'Plate' if 'Plate' in objects_held else objects_held[0]

    @staticmethod
    def _check_object_on_a_plate(env_state, object_position):
        """Returns true if the object at the given object_position is on a plate"""
        return env_state[tuple(object_position)][MAP_OBJECT_TO_NUMBER['Plate']]

    @staticmethod
    def check_any_object_on_a_plate(env_state, object_plane_index):
        """Returns true if any object of the given object_plane is on a plate"""
        object_plane = env_state[:, :, object_plane_index]
        return np.sum(np.logical_and(env_state[:, :, MAP_OBJECT_TO_NUMBER['Plate']], object_plane)) > 0

    @staticmethod
    def check_any_object_on_a_cutboard(env_state, object_plane_index):
        """Returns true if any object of the given object_plane is on a cutboard"""
        object_plane = env_state[:, :, object_plane_index]
        return np.sum(np.logical_and(env_state[:, :, MAP_OBJECT_TO_NUMBER['Cutboard']], object_plane)) > 0

    @staticmethod
    def _check_agent_at_goal_position(agent_pos, goal_positions):
        """
        checks if the agent is at one of the goal positions
        :param np.array agent_pos: current position of the array
        :param list goal_positions: list with all goal positions
        :return: True if agent is at one of the goal positions
        """
        return tuple(agent_pos) in goal_positions

    @staticmethod
    def _check_object_exists(feature_plane):
        """
        checks if an entry of the feature plane is 1 and the object therefore exists
        :param feature_plane: feature plane
        :return: True if object exists
        """
        return 1 in feature_plane

    @staticmethod
    def _get_object_positions(feature_plane):
        """
        returns all positions where the entry in the feature plane is 1
        :param feature_plane: feature plane
        :return: list with all positions
        """
        goal_positions = []
        for (x, y), value in np.ndenumerate(feature_plane):
            if value == 1:
                goal_positions.append((x, y))
        return goal_positions

    def _get_mutual_available_counters(self, env_state):
        """Returns a list of all counter positions that are reachable by at least two agents. Agents are ignored as obstacles so a path may not exist,
        even if a field is available."""
        mutual_fields = []
        counter_plane = env_state[:, :, MAP_OBJECT_TO_NUMBER['Counter']]
        # check all fields except those at the wall
        for x in range(1, counter_plane.shape[0] - 1):
            for y in range(1, counter_plane.shape[1] - 1):
                if counter_plane[x, y] == 1:
                    # check if the counter is free
                    # print(x, y)
                    # print(env_state[x, y])
                    # if np.sum(env_state[x, y]) == 1:
                    if self._check_field_is_mutually_available(env_state, (x, y)):
                        mutual_fields.append((x, y))
        return mutual_fields

    def check_object_is_on_mutually_available_field(self, env_state, object_plane):
        """Returns true if one object from the given object plane is available for at least two agents"""
        obj_positions = self._get_object_positions(object_plane)
        for obj_pos in obj_positions:
            if self._check_field_is_mutually_available(env_state, obj_pos):
                return True
        return False

    def _check_field_is_mutually_available(self, env_state, position):
        """Returns true if the given position is basically reachable for at least two agents. The Path may still be blocked by
        other agents as these are ignored!"""
        agent_positions = self._get_object_positions(env_state[:, :, MAP_OBJECT_TO_NUMBER['Agent']])
        n_agents_reaching_position = 0
        self.motion_generator.reset(env_state, self.motion_generator.agent_position, ignore_agents_as_obstacles=True)
        for agent_pos in agent_positions:
            if self._check_field_is_reachable(position, agent_pos):
                n_agents_reaching_position += 1

        return n_agents_reaching_position > 1

    @staticmethod
    def _check_fields_next_to_each_other(field_pos1, field_pos2):
        """Returns true if the two given fields are neighbors"""
        diff = np.abs(np.array(field_pos1) - np.array(field_pos2))
        return diff[0] == 0 and diff[1] == 1 or diff[0] == 1 and diff[1] == 0

    def _check_field_is_reachable(self, goal_pos, start_pos):
        """Returns true if the given goal_pos is reachable from position start_pos. Agents are seens as obstacles as well."""
        goal_pos = tuple(goal_pos)
        start_pos = tuple(start_pos)
        return self.motion_generator.shortest_path(start_pos, goal_pos)[0] is not None \
               or self._check_fields_next_to_each_other(goal_pos, start_pos) or goal_pos == start_pos

    def check_object_is_reachable(self, env_state, object_plane_index, start_pos):
        """Returns true if an object from the given object plane is reachable from the start_position.
        ATTENTION: if an object is on a plate, it is not 'reachable' in that sense, since only the plate is reachable then.
        ##In the same sense a cutboard is only reachable if it is not occupied!"""
        object_plane = env_state[:, :, object_plane_index]
        if not self._check_object_exists(object_plane):
            return False

        # if start_pos is on object plane, e.g. agent is holding the object
        if object_plane[tuple(start_pos)] == 1 and not self._check_object_on_a_plate(env_state, start_pos):
            return True

        object_positions = self._get_object_positions(object_plane)
        for obj_pos in object_positions:

            # continue if object is on a plate
            if object_plane_index != MAP_OBJECT_TO_NUMBER['Plate']:
                if self._check_object_on_a_plate(env_state, obj_pos):
                    continue

            # continue if the object is a cutboard and occupied
            if object_plane_index == MAP_OBJECT_TO_NUMBER['CutBoard']:
                if self._check_multiple_objects_at_position(env_state, obj_pos):
                    continue

            # return true if object is not on a plate and reachable
            if self._check_field_is_reachable(obj_pos, start_pos):
                return True
        return False

    @staticmethod
    def _create_plane_from_positions(positions, plane_shape):
        """Returns a (feature) plane of the given shape, with 1s on all of the given positions."""
        plane = np.zeros(plane_shape)
        for pos in positions:
            plane[pos] = 1
        return plane

    @staticmethod
    def _get_free_counters(env_state):
        """Returns a feature map representing all free counters."""
        counter_plane = env_state[:, :, MAP_OBJECT_TO_NUMBER['Counter']]
        occupied_fields = np.sum(env_state[:, :, 2:], axis=2)
        occupied_fields = np.clip(occupied_fields, 0, 1)
        free_counters = np.logical_and(counter_plane, np.logical_not(occupied_fields))
        return free_counters

    #checks whether the given high level task will be finished using an action
    def task_finished(self, task, action, env_state, agent_pos):
        if(task in ActionTypes.PROCESS.value):
            if action == 0:
                return True
            else:
                return False
        if (task in ActionTypes.GIVE.value):
            if action == 5:
                if self._check_multiple_objects_at_position(env_state, agent_pos):
                    held_object = self._get_object_held_by_agent(env_state, agent_pos)
                    if str(held_object) == MAP_ACTIONS_TO_OBJECTS[task][1]:
                        return True
            else:
                if action == 0:
                    objects = MAP_ACTIONS_TO_OBJECTS[task]
                    object_plane_index = MAP_OBJECT_TO_NUMBER[objects[1]]
                    object_plane = env_state[:, :, object_plane_index]
                    if (not self._check_object_exists(object_plane)):
                        return True
                return False
        if (task in ActionTypes.DELIVER.value):
            if action == 0:
                return True
            else:
                return False
        if (task in ActionTypes.PLATE.value):
            if action == 0:
                return True
            else:
                return False
            pass


