#! /usr/bin/env python3
import argparse
from enum import Enum
import copy
import random
from typing import List, Tuple, Callable

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

    def player_pos(self):
        active_field = self.active_field()
        for x in range (self.width):
            for y in range (self.height):
                if active_field[x][y] == Tile.PLAYER:
                    return (x, y)

    def tile(self, pos: Position):
        if pos[0] < 0 or pos[0] >= self.width:
            return Tile.OUT_OF_BOUNDS
        if pos[1] < 0 or pos[1] >= self.height:
            return Tile.OUT_OF_BOUNDS
        active_field = self.active_field()
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


        every_outcome_was_nothing = False
        while not every_outcome_was_nothing:
            next_entities = []
            for entity in entities:
                next_entity = self.apply_direction_to_entity(dir_func, entity[1])
                if next_entity[0].is_ending():
                    return next_entity[0]
                next_entities.append(next_entity)
            entities = next_entities;
            every_outcome_was_nothing = all(outcome == MoveOutcome.NOTHING for (outcome, _) in entities)

        return MoveOutcome.NOTHING

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

        self.old_field = self.active_field()
        self.set_tile(player_pos, Tile.BLANK)
        self.active_player = self.active_player.change()

        if self.is_stopping(player_pos):
            return MoveOutcome.PLAYER_CRUSHED
        if self.is_killing(player_pos):
            return MoveOutcome.PLAYER_KILLED

        self.set_tile(player_pos, Tile.PLAYER)
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
            self.field_white = [[Tile.BLANK for x in range(width)] for y in range(height)] 
            self.field_black = [[Tile.BLANK for x in range(width)] for y in range(height)]
            self.active_player = ActivePlayer.WHITE
            self.exit_pos = exit_pos
        else:
            assert(move is not None)
            
            self.width = state.width
            self.height = state.height
            self.field_black = copy.deepcopy(state.field_black)
            self.field_white = copy.deepcopy(state.field_white)
            self.active_player = state.active_player
            self.exit_pos = state.exit_pos
            self.outcome = self.move_switch[move](self)

    def field_to_str(self, field):
        s = ["" for x in range(self.height)]
        
        for x in range (self.width):
            for y in range (self.height):
                s[y] += str(field[x][y])

        return '\n'.join(s)
        
    def __str__(self):
        return " White Field:\n{}\n Black Field:\n{}\n Outcome: {}\n Exit: ({},{})".format(
            self.field_to_str(self.field_white),
            self.field_to_str(self.field_black),
            self.outcome,
            self.exit_pos[0], self.exit_pos[1])
 
class LevelDescription:
    width = 4
    height = 4
    enable_spiral = False
    enable_enemy = False

    start_state: LevelState

    def __init__(self, width : int = 4, height : int = 4, enable_spiral : bool = False, enable_enemy : bool = False):
        self.width = width
        self.height = height
        self.enable_spiral = enable_spiral
        self.enable_enemy = enable_enemy

        end_pos_x = random.randrange(-1, width + 1)
        end_pos_y = 0
        if end_pos_x == -1 or end_pos_x == width:
            end_pos_y = random.randrange(height)
        else:
            end_pos_y = random.choice([-1, height])
        self.exit_pos=(end_pos_x, end_pos_y)

        self.state = LevelState(width=width, height=height, exit_pos=self.exit_pos)

    def compute_possible_sources(self, player_pos, state):
        sources = []
        
        left = player_pos[0] > 0 and 0 <= player_pos[1] and player_pos[1] < self.height
        right = player_pos[0] < self.width and 0 <= player_pos[1] and player_pos[1] < self.height
        up = player_pos[1] > 0 and 0 <= player_pos[0] and player_pos[0] < self.width
        down = player_pos[1] < self.height and 0 <= player_pos[0] and player_pos[0] < self.width

        if left:
            for x in range (0, player_pos[0]):
                sources.append(((x, player_pos[1]), (player_pos[0] + 1, player_pos[1]), Move.RIGHT))
        if right:
            for x in range (player_pos[0], self.width):
                sources.append(((x, player_pos[1]), (player_pos[0] - 1, player_pos[1]), Move.LEFT))
        if up:
            for y in range (0, player_pos[1]):
                sources.append(((player_pos[0], y), (player_pos[0], player_pos[1] + 1), Move.DOWN))
        if down:
            for y in range (player_pos[1], self.height):
                sources.append(((player_pos[0], y), (player_pos[0], player_pos[1] - 1), Move.UP))

        return sources;

    def generate_with_player_from_exit_pos(self, steps: int):
        self.player_pos = self.exit_pos
        self.moves = []

        while steps > 0:
            sources = self.compute_possible_sources(self.player_pos, self.state)

            source, stopper, move = random.choice(sources)

            if self.state.tile(stopper) != Tile.OUT_OF_BOUNDS:
                self.state.set_tile(stopper, Tile.BLOCK)

            self.player_pos = source
            self.moves.insert(0, move)

            steps -= 1

    def __str__(self):
        return str(self.state) + "\n Moves: " + str(self.moves) + "\n Start: " + str(self.player_pos)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate levels for ShadeChange.')
    parser.add_argument('--width', help='level width', default=4, type=int)
    parser.add_argument('--height', help='level height', default=4, type=int)
    parser.add_argument('--steps', help='number of steps a level should take', default=3, type=int)
    parser.add_argument('--enable-spiral', help='enable the spiral tile type', default=False, action="store_true")
    parser.add_argument('--enable-enemy', help='enable the enemy entity', default=False, action="store_true")
    args = parser.parse_args()

    level = LevelDescription(width=args.width, height=args.height, enable_enemy=args.enable_enemy, enable_spiral=args.enable_spiral)
    level.generate_with_player_from_exit_pos(args.steps)

    print(level)
