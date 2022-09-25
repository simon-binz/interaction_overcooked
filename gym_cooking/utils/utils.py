import numpy as np


MAP_NUMBER_TO_OBJECT = {
    0: 'Floor',
    1: 'Counter',
    2: 'CutBoard',
    3: 'DeliverSquare',
    4: 'Tomato',
    5: 'ChoppedTomato',
    6: 'Lettuce',
    7: 'ChoppedLettuce',
    8: 'Onion',
    9: 'ChoppedOnion',
    10: 'Plate',
    11: 'Blender',
    12: 'Carrot',
    13: 'ChoppedCarrot',
    14: 'MashedCarrot',  # (or switch with ChoppedCarrot?)
    15: 'Agent',
    16: 'AgentOriented1 (West)',
    17: 'AgentOriented2 (East)',
    18: 'AgentOriented3 (South)',
    19: 'AgentOriented4 (North)'
}

MAP_OBJECT_TO_NUMBER = {v: k for k, v in MAP_NUMBER_TO_OBJECT.items()}

ACTION_MAP = {
    'nop': 0,
    'move_left': 1,
    'move_right': 2,
    'move_down': 3,
    'move_up': 4,
    'interact': 5
}

ACTIONS_INTENTIONS_MAP = {
    'nop': 'Skip',
    'move_left': 'Left',
    'move_right': 'Right',
    'move_down': 'Down',
    'move_up': 'Up',
    'interact': 'F'
}






def correct_fm_tensor(fm):
    """Corrects the given tensor to be aligned with the game window (transposed)."""
    return np.transpose(fm, axis=2)
