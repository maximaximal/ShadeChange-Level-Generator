#! /usr/bin/env python3
import argparse
from enum import Enum
import copy
import random
from typing import List, Tuple, Callable, Set

Position = Tuple[int, int]

def up(pos: Position) -> Position:
    return (pos[0], pos[1] - 1)
def down(pos: Position) -> Position:
    return (pos[0], pos[1] + 1)
def left(pos: Position)  -> Position:
    return (pos[0] - 1, pos[1])
def right(pos: Position) -> Position:
    return (pos[0] + 1, pos[1])

MovementFunction = Callable[[Position], Position]

class Tile(Enum):
    OUT_OF_BOUNDS = 0
    BLANK = 1
    BLOCK = 2
    SPIRAL = 3
    ENEMY = 4
    PLAYER = 5

    def __str__(self):
        if self == self.BLANK:
            return '.'
        if self == self.BLOCK:
            return '#'
        if self == self.SPIRAL:
            return '@'
        if self == self.ENEMY:
            return '!'
        if self == self.PLAYER:
            return 'p'
        return '?'

class Move(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    CHANGE = 5
    def __str__(self):
        return {
            self.UP: "↑",
            self.DOWN: "↓",
            self.LEFT: "←",
            self.RIGHT: "→",
            self.CHANGE: "⇄"
            }[self]

class MoveOutcome(Enum):
    UNDETERMINED = 1
    NOTHING = 2
    MOVED = 3
    CHANGED = 4
    PLAYER_WON = 5
    ENEMY_WON = 6
    PLAYER_CRUSHED = 7
    PLAYER_KILLED = 8

    def is_ending(self):
        return self in [self.PLAYER_WON, self.PLAYER_KILLED, self.PLAYER_CRUSHED, self.ENEMY_WON]

class ActivePlayer(Enum):
    WHITE = 1
    BLACK = 2
    def change(self):
        return self.WHITE if self == self.BLACK else self.BLACK

class LevelState:
    field_white = None
    field_black = None
    active_player = None
    outcome = MoveOutcome.UNDETERMINED
    exit_pos: Position

    width : int
    height : int

    def active_field(self, flipped=False):
        active_player = self.active_player

        if flipped:
            active_player = active_player.change()

        if active_player == ActivePlayer.WHITE:
            return self.field_white
        if active_player == ActivePlayer.BLACK:
            return self.field_black

    def player_pos(self) -> Position:
        active_field = self.active_field()
        pos = [-1, -1]
        for x in range (self.width):
            for y in range (self.height):
                if active_field[x][y] == Tile.PLAYER:
                    assert(pos[0] == -1 and pos[1] == -1)
                    pos[0] = x
                    pos[1] = y

        assert(pos[0] != -1 and pos[1] != -1)
        return pos

    def tile(self, pos: Position):
        if pos[0] < 0 or pos[0] >= self.width:
            return Tile.OUT_OF_BOUNDS
        if pos[1] < 0 or pos[1] >= self.height:
            return Tile.OUT_OF_BOUNDS
        active_field = self.active_field()
        return active_field[pos[0]][pos[1]]

    def changed_tile(self, pos: Position):
        if pos[0] < 0 or pos[0] >= self.width:
            return Tile.OUT_OF_BOUNDS
        if pos[1] < 0 or pos[1] >= self.height:
            return Tile.OUT_OF_BOUNDS
        active_field = self.active_field(flipped=True)
        return active_field[pos[0]][pos[1]]

    def set_tile(self, pos: Position, tile: Tile, flipped=False):
        assert(pos[0] >= 0 and pos[0] < self.width and pos[1] >= 0 or pos[1] < self.height)
        active_field = self.active_field(flipped)
        active_field[pos[0]][pos[1]] = tile

    def is_stopping(self, pos: Position):
        active_field = self.active_field()
        tile = self.tile(pos)
        return tile in [Tile.OUT_OF_BOUNDS, Tile.BLOCK]

    def is_killing(self, pos: Position):
        active_field = self.active_field()
        tile = self.tile(pos)
        return tile in [Tile.ENEMY, Tile.SPIRAL]

    def apply_direction_to_entity(self, dir_func = MovementFunction, start_pos = Position) -> Tuple[MoveOutcome, Position]:
        player = self.tile(start_pos) == Tile.PLAYER
        enemy = self.tile(start_pos) == Tile.ENEMY
        assert(player or enemy)

        next_pos = dir_func(start_pos)

        # Winning conditions first. Nothing has to be changed in that case.
        if player and next_pos == self.exit_pos:
            return (MoveOutcome.PLAYER_WON, start_pos)
        if player and self.is_killing(next_pos):
            return (MoveOutcome.PLAYER_KILLED, start_pos)
        if enemy and self.tile(next_pos) == Tile.PLAYER:
            return (MoveOutcome.PLAYER_KILLED, start_pos)
        if enemy and next_pos == self.exit_pos:
            return (MoveOutcome.ENEMY_WON, start_pos)

        # Stopped, but no winning condition triggered.
        if self.is_stopping(next_pos):
            return (MoveOutcome.NOTHING, start_pos)

        # Not stopped or killed, moving may continue.
        self.set_tile(next_pos, self.tile(start_pos))
        self.set_tile(start_pos, Tile.BLANK)
            
        return (MoveOutcome.MOVED, next_pos)

    def apply_direction(self, dir_func = MovementFunction) -> MoveOutcome:
        # Directions have to be applied to all entities, as long as
        # stuff keeps happening. First, all entities have to be found. Then,
        # directions are applied.

        entities: List[Tuple[MoveOutcome, Position]] = []
        active_field = self.active_field()
        
        # Find all entities
        for x in range (self.width):
            for y in range (self.height):
                if active_field[x][y] in [Tile.PLAYER, Tile.ENEMY]:
                    entities.append((MoveOutcome.UNDETERMINED, (x, y)))


        moved_once = False
        every_outcome_was_nothing = False
        while not every_outcome_was_nothing:
            next_entities = []
            for entity in entities:
                next_entity = self.apply_direction_to_entity(dir_func, entity[1])
                if next_entity[0].is_ending():
                    return next_entity[0]
                if next_entity[0] == MoveOutcome.MOVED:
                    moved_once = True
                next_entities.append(next_entity)
            entities = next_entities;
            every_outcome_was_nothing = all(outcome == MoveOutcome.NOTHING for (outcome, _) in entities)

        return MoveOutcome.MOVED if moved_once else MoveOutcome.NOTHING

    def apply_UP(self) -> MoveOutcome:
        return self.apply_direction(up)
    def apply_DOWN(self) -> MoveOutcome:
        return self.apply_direction(down)
    def apply_LEFT(self) -> MoveOutcome:
        return self.apply_direction(left)
    def apply_RIGHT(self) -> MoveOutcome:
        return self.apply_direction(right)
    def apply_CHANGE(self) -> MoveOutcome:
        player_pos = self.player_pos()
        assert(player_pos is not None)

        self.set_tile(player_pos, Tile.BLANK)
        self.active_player = self.active_player.change()

        if self.is_stopping(player_pos):
            return MoveOutcome.PLAYER_CRUSHED
        if self.is_killing(player_pos):
            return MoveOutcome.PLAYER_KILLED

        self.set_tile(player_pos, Tile.PLAYER)

        assert(self.tile(player_pos) == Tile.PLAYER)
        
        return MoveOutcome.CHANGED
        
    move_switch = {
        Move.UP: apply_UP,
        Move.DOWN: apply_DOWN,
        Move.LEFT: apply_LEFT,
        Move.RIGHT: apply_RIGHT,
        Move.CHANGE: apply_CHANGE
    }

    def __init__(self, state = None, move: Move = None, width: int = None, height: int = None, exit_pos: Position = None):
        if state == None:
            assert(width is not None and  height is not None and exit_pos is not None)
            assert((exit_pos[0] == -1 and 0 <= exit_pos[1] < height) or
                (exit_pos[0] == width and 0 <= exit_pos[1] < height) or
                (exit_pos[1] == -1 and 0 <= exit_pos[0] < width) or
                (exit_pos[1] == height and 0 <= exit_pos[0] < width))

            self.width = width
            self.height = height
            self.field_white = [[Tile.BLANK for x in range(height)] for y in range(width)] 
            self.field_black = [[Tile.BLANK for x in range(height)] for y in range(width)]
            self.active_player = ActivePlayer.WHITE
            self.exit_pos = exit_pos
        else:
            self.width = state.width
            self.height = state.height
            self.field_black = copy.deepcopy(state.field_black)
            self.field_white = copy.deepcopy(state.field_white)
            self.active_player = state.active_player
            self.exit_pos = state.exit_pos

        if move is not None:
            self.outcome = self.move_switch[move](self)

    def field_to_str(self, field):
        s = ["" for x in range(self.height)]
        
        for x in range (self.width):
            for y in range (self.height):
                s[y] += str(field[x][y])

        return '\n'.join(s)
        
    def __str__(self):
        return " White Field (1):\n{}\n Black Field (0):\n{}\n Outcome: {}\n Exit: ({},{})".format(
            self.field_to_str(self.field_white),
            self.field_to_str(self.field_black),
            self.outcome,
            self.exit_pos[0], self.exit_pos[1])

    def to_list(self):
        s = ""
        for x in range (self.width):
            for y in range (self.height):
                s += str(x) + "," + str(y) + "," + str(self.field_white[x][y].value) + '\n'
        s += "\n"
        for x in range (self.width):
            for y in range (self.height):
                s += str(x) + "," + str(y) + "," + str(self.field_white[x][y].value) + '\n'
        s += "\n"
        p = self.player_pos()
        s += str(p[0]) + "," + str(p[1]) + "," + ("1" if self.active_player == ActivePlayer.WHITE else "0")
        s += "\n\n"
        s += str(self.exit_pos[0]) + "," + str(self.exit_pos[1])
        return s

class BotPlayerSearcher:
    def __init__(self, state: LevelState, start_pos: Position, max_depth: int):
        assert(start_pos[0] >= 0 and start_pos[0] < state.width)
        assert(start_pos[1] >= 0 and start_pos[1] < state.height)
        assert(state is not None)
        
        self.state = state;
        self.state.set_tile(start_pos, Tile.PLAYER)
        self.path = []
        self.max_depth = max_depth

    def do_search(self):
        assert(self.state is not None)
        return self.search(self.state, 0)

    def search(self, state: LevelState, depth: int ):
        assert(state is not None)

        if depth > self.max_depth:
            return None
        if state.outcome == MoveOutcome.PLAYER_WON:
            return state
        if state.outcome.is_ending():
            return None

        for move in Move:
            next_state = LevelState(state, move)
            assert(next_state is not None)
            self.path.append(move)
            next_step = self.search(next_state, len(self.path))
            if next_step is not None:
                return next_step
            self.path.pop()

        return None
    
class BotPlayer:
    def __init__(self, state: LevelState, start_pos: Position = None, desired_depth: int = -1):
        if start_pos is None:
            self.start_pos = state.player_pos()
        else:
            self.start_pos = start_pos

        assert(self.start_pos[0] >= 0 and self.start_pos[0] < state.width)
        assert(self.start_pos[1] >= 0 and self.start_pos[1] < state.height)
        assert(state is not None)
        
        self.state = state;

        self.desired_depth = desired_depth

    def search_path_ids(self):
        for max_depth in range(1, 100):
            searcher = BotPlayerSearcher(self.state, self.start_pos, max_depth)
            if searcher.do_search() is not None:
                return searcher.path

        return False

class LevelSearcherConfig:
    width: int = 4 # Constant
    height: int = 4 # Constant
    move_count: int = 5 # Constant
    spirals: int = 0 # Shrinking
    enemies: int = 0 # Shrinking
    moves: int = 0 # Growing
    changes: int = 1 # Shrinking
    blocks: int = 1 # Shrinking

class GeneratorAction:
    move: Move = None

    def do(self, state: LevelState, config: LevelSearcherConfig):
        pass

    def undo(self, state: LevelState, config: LevelSearcherConfig):
        pass

    def get_moves(actions):
        moves = []
        for action in actions:
            if action.move is not None:
                moves.append(action.move)
        return moves

    def __str__(self):
        return "GeneratorAction"

class GeneratorMovementAction(GeneratorAction):
    def __init__(self, player_pos: Position, source: Position, stopper: Position, move: Move):
        self.source = source
        self.stopper = stopper
        self.move = move
        self.orig_stopper_tile = None
        self.player_pos = player_pos

    def do(self, state: LevelState, config: LevelSearcherConfig):
        assert(state.tile(self.source) == Tile.BLANK)
        
        tile = state.tile(self.stopper)
        if tile != Tile.OUT_OF_BOUNDS:
            self.orig_stopper_tile = tile
            state.set_tile(self.stopper, Tile.BLOCK)

        if(state.tile(self.player_pos) != Tile.OUT_OF_BOUNDS):
            state.set_tile(self.player_pos, Tile.BLANK)

        state.set_tile(self.source, Tile.PLAYER)

        config.moves += 1
        
    def undo(self, state: LevelState, config: LevelSearcherConfig):
        if self.orig_stopper_tile is not None:
            state.set_tile(self.stopper, self.orig_stopper_tile)

        state.set_tile(self.source, Tile.BLANK)

        if(state.tile(self.player_pos) != Tile.OUT_OF_BOUNDS):
            state.set_tile(self.player_pos, Tile.PLAYER)

        config.moves -= 1

    def __str__(self):
        return "(" + str(self.move) + ", source=" + str(self.source) + ", stopper=" + str(self.stopper) + ")"

class GeneratorChangeAction:
    def __init__(self):
        self.move = Move.CHANGE

    def do(self, state: LevelState, config: LevelSearcherConfig):
        player_pos = state.player_pos()
        state.set_tile(player_pos, Tile.BLANK)
        state.active_player = state.active_player.change()
        state.set_tile(player_pos, Tile.PLAYER)
        config.changes -= 1

    def undo(self, state: LevelState, config: LevelSearcherConfig):
        player_pos = state.player_pos()
        state.set_tile(player_pos, Tile.BLANK)
        state.active_player = state.active_player.change()
        state.set_tile(player_pos, Tile.PLAYER)
        config.changes += 1

class GeneratorBlockAction:
    def __init__(self, pos: Position):
        self.pos = pos
        self.move = None

    def do(self, state: LevelState, config: LevelSearcherConfig):
        state.set_tile(self.pos, Tile.BLOCK)
        config.blocks -= 1

    def undo(self, state: LevelState, config: LevelSearcherConfig):
        state.set_tile(self.pos, Tile.BLANK)
        config.blocks += 1

class GeneratorEnemyAction:
    def __init__(self, pos: Position):
        self.pos = pos
        self.move = None

    def do(self, state: LevelState, config: LevelSearcherConfig):
        assert(config.enemies > 0)
        state.set_tile(self.pos, Tile.ENEMY)
        config.enemies -= 1

    def undo(self, state: LevelState, config: LevelSearcherConfig):
        state.set_tile(self.pos, Tile.BLANK)
        config.enemies += 1

class GeneratorSpiralAction:
    def __init__(self, pos: Position):
        self.pos = pos
        self.move = None

    def do(self, state: LevelState, config: LevelSearcherConfig):
        assert(config.spirals > 0)
        state.set_tile(self.pos, Tile.SPIRAL)
        config.spirals -= 1

    def undo(self, state: LevelState, config: LevelSearcherConfig):
        state.set_tile(self.pos, Tile.BLANK)
        config.spirals += 1

class LevelSearcher:
    def get_random_exit_pos(width: int, height: int) -> Position:
        end_pos_x = random.randrange(-1, width + 1)
        end_pos_y = 0
        if end_pos_x == -1 or end_pos_x == width:
            end_pos_y = random.randrange(height)
        else:
            end_pos_y = random.choice([-1, height])
        return (end_pos_x, end_pos_y)
    
    def __init__(self, config: LevelSearcherConfig):
        self.width = config.width
        self.height = config.height
        self.config = config
        self.max_depth = 1
        self.player_pos = [0, 0]

        exit_pos = LevelSearcher.get_random_exit_pos(self.width, self.height)
        self.level = LevelState(width=self.width, height=self.height, exit_pos=exit_pos)

    def expand_moves(self, state: LevelState, player_pos: Position):
        actions = []
        
        left = player_pos[0] > 0 and 0 <= player_pos[1] and player_pos[1] < self.height
        right = player_pos[0] < self.width and 0 <= player_pos[1] and player_pos[1] < self.height
        up = player_pos[1] > 0 and 0 <= player_pos[0] and player_pos[0] < self.width
        down = player_pos[1] < self.height and 0 <= player_pos[0] and player_pos[0] < self.width

        if left:
            for x in range (0, player_pos[0]):
                if state.is_stopping((x, player_pos[1])) or state.is_killing((x, player_pos[1])):
                    continue
                actions.append(GeneratorMovementAction(player_pos, (x, player_pos[1]), (player_pos[0] + 1, player_pos[1]), Move.RIGHT))
        if right:
            for x in range (player_pos[0] + 1, self.width):
                if state.is_stopping((x, player_pos[1])) or state.is_killing((x, player_pos[1])):
                    continue
                actions.append(GeneratorMovementAction(player_pos, (x, player_pos[1]), (player_pos[0] - 1, player_pos[1]), Move.LEFT))
        if up:
            for y in range (0, player_pos[1]):
                if state.is_stopping((player_pos[0], y)) or state.is_killing((player_pos[0], y)):
                    continue
                actions.append(GeneratorMovementAction(player_pos, (player_pos[0], y), (player_pos[0], player_pos[1] + 1), Move.DOWN))
        if down:
            for y in range (player_pos[1] + 1, self.height):
                if state.is_stopping((player_pos[0], y)) or state.is_killing((player_pos[0], y)):
                    continue
                actions.append(GeneratorMovementAction(player_pos, (player_pos[0], y), (player_pos[0], player_pos[1] - 1), Move.UP))

        return actions

    def expand(self, state: LevelState, running_config: LevelSearcherConfig):
        actions = []
        
        # Spiral & Enemy
        if running_config.enemies > 0 or running_config.spirals > 0 or running_config.blocks > 0:
            for x in range(self.width):
                for y in range(self.height):
                    pos = (x, y)
                    if not state.is_killing(pos) and not state.is_stopping(pos) and state.tile(pos) != Tile.PLAYER:
                        if running_config.spirals > 0:
                            actions.append(GeneratorSpiralAction(pos))
                        if running_config.enemies > 0:
                            actions.append(GeneratorEnemyAction(pos))
                        if running_config.blocks:
                            actions.append(GeneratorBlockAction(pos))

        # Movement
        if running_config.moves == 0:
            player_pos = state.exit_pos
        else:
            player_pos = state.player_pos()

            # Change
            if running_config.changes > 0:
                changed_tile = state.changed_tile(player_pos)
                if changed_tile not in [Tile.BLOCK, Tile.ENEMY, Tile.SPIRAL]:
                    actions.append(GeneratorChangeAction())

        actions.extend(self.expand_moves(state, player_pos))

        return actions

    def is_done(self, state: LevelState, actions: List[GeneratorAction], config: LevelSearcherConfig) -> bool:
        moves = GeneratorAction.get_moves(actions)
        if len(moves) != config.move_count:
            return False

        if config.spirals > 0:
            return False

        if config.enemies > 0:
            return False

        if config.changes > 0:
            return False

        # Check if moves lead to winning.
        s = state
        winning = False
        for m in moves:
            s = LevelState(state=s, move=m)
            outcome = s.outcome
            if outcome.is_ending() and outcome != MoveOutcome.PLAYER_WON:
                return False

        # Check if there is any shorter way
        bot = BotPlayer(copy.deepcopy(state), state.player_pos(), len(moves))
        shortest_path = bot.search_path_ids()

        # No solution found!
        if not shortest_path:
            return False

        if len(shortest_path) != config.move_count:
            return False

        return True

    def search(self):
        result = None

        while result is None:
            self.max_depth += 1
            result = self.inner_search(self.config)

        return (self.level, GeneratorAction.get_moves(result))
        
    def inner_search(self, running_config: LevelSearcherConfig, depth: int = 0, actions: List[GeneratorAction] = []) -> List[GeneratorAction]:
        # IDS search
        if depth > self.max_depth:
            return None
        
        # If we are done, return and end search
        if self.is_done(self.level, actions, running_config):
            return actions

        # If we still have to search, expand actions.
        available_actions = self.expand(self.level, running_config)

        # Select random action, apply it and do recursion.
        while len(available_actions) > 0:
            selected_action = random.choice(available_actions)
            available_actions.remove(selected_action)
            actions.insert(0, selected_action)

            selected_action.do(self.level, running_config)

            search_result = self.inner_search(running_config, depth + 1, actions)
            if search_result is not None:
                return search_result
            else:
                selected_action.undo(self.level, running_config)
                actions.pop(0)

        return None
    
class LevelDescription:
    width = 4
    height = 4
    enable_spiral = False
    enable_enemy = False

    start_state: LevelState

    def __init__(self, width : int = 4, height : int = 4, enable_spiral : bool = False, enable_enemy : bool = False, changes: int = 1, blocks: int = 1):
        self.width = width
        self.height = height
        self.enable_spiral = enable_spiral
        self.enable_enemy = enable_enemy
        self.changes = changes
        self.blocks = blocks

    def generate_with_player_from_exit_pos(self, steps: int):
        config = LevelSearcherConfig()
        config.width = self.width
        config.height = self.height
        config.enemies = 1 if self.enable_enemy else 0
        config.spirals = 1 if self.enable_spiral else 0
        config.move_count = steps
        config.changes = self.changes
        config.blocks = self.blocks

        searcher = LevelSearcher(config)
        self.state, self.moves = searcher.search()
        self.player_pos = self.state.player_pos()

    def __str__(self):
        return str(self.state) + "\n Moves: " + ", ".join(map(str, self.moves)) + "\n Start: " + str(self.player_pos)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate levels for ShadeChange.')
    parser.add_argument('--width', help='level width', default=4, type=int)
    parser.add_argument('--height', help='level height', default=4, type=int)
    parser.add_argument('--steps', help='number of steps a level should take', default=5, type=int)
    parser.add_argument('--changes', help='number of changes a level should include', default=1, type=int)
    parser.add_argument('--blocks', help='number of randomly set blocks a level may include', default=1, type=int)
    parser.add_argument('--enable-spiral', help='enable the spiral tile type', default=False, action="store_true")
    parser.add_argument('--enable-enemy', help='enable the enemy entity', default=False, action="store_true")
    parser.add_argument('--print-list', help='print output to list. First section is white board, second is black.', default=False, action="store_true")
    parser.add_argument('--print-human-readable', help='print human readable output', default=True, action="store_true")
    args = parser.parse_args()

    level = LevelDescription(width=args.width, height=args.height, enable_enemy=args.enable_enemy, enable_spiral=args.enable_spiral, changes=args.changes, blocks=args.blocks)
    level.generate_with_player_from_exit_pos(args.steps)

    if args.print_human_readable:
        print(level)
        print("\n")
    if args.print_list:
        print(level.state.to_list())

