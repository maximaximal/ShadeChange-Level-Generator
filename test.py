#! /usr/bin/env python3
import unittest
import generator

class TestLevelState(unittest.TestCase):
    def test_player_wins(self):
        state = generator.LevelState(width=4, height=4, exit_pos=(0, -1))
        state.set_tile((0, 3), generator.Tile.PLAYER)
        new_state = generator.LevelState(state=state, move=generator.Move.UP)
        self.assertEqual(new_state.outcome, generator.MoveOutcome.PLAYER_WON)

    def test_left_nothing(self):
        state = generator.LevelState(width=4, height=4, exit_pos=(0, -1))
        state.set_tile((0, 0), generator.Tile.PLAYER)
        new_state = generator.LevelState(state=state, move=generator.Move.LEFT)
        self.assertEqual(new_state.outcome, generator.MoveOutcome.NOTHING)

    def test_right_blocked(self):
        state = generator.LevelState(width=4, height=4, exit_pos=(0, -1))
        state.set_tile((0, 0), generator.Tile.PLAYER)
        state.set_tile((2, 0), generator.Tile.BLOCK)
        new_state = generator.LevelState(state=state, move=generator.Move.RIGHT)
        self.assertEqual(new_state.outcome, generator.MoveOutcome.MOVED)

        new_state = generator.LevelState(state=new_state, move=generator.Move.RIGHT)
        self.assertEqual(new_state.outcome, generator.MoveOutcome.NOTHING)
        self.assertEqual(new_state.tile((1, 0)), generator.Tile.PLAYER)

    def test_crushed(self):
        state = generator.LevelState(width=4, height=4, exit_pos=(0, -1))
        state.set_tile((0, 0), generator.Tile.PLAYER)
        state.set_tile((3, 0), generator.Tile.BLOCK)
        state.set_tile((2, 0), generator.Tile.BLOCK, flipped=True)
        new_state = generator.LevelState(state=state, move=generator.Move.RIGHT)
        self.assertEqual(new_state.outcome, generator.MoveOutcome.MOVED)

        new_state = generator.LevelState(state=new_state, move=generator.Move.CHANGE)
        self.assertEqual(new_state.outcome, generator.MoveOutcome.PLAYER_CRUSHED)

    def test_killed(self):
        state = generator.LevelState(width=4, height=4, exit_pos=(0, -1))
        state.set_tile((0, 0), generator.Tile.PLAYER)
        state.set_tile((2, 0), generator.Tile.ENEMY)
        new_state = generator.LevelState(state=state, move=generator.Move.RIGHT)
        self.assertEqual(new_state.outcome, generator.MoveOutcome.PLAYER_KILLED)
        self.assertEqual(new_state.tile((3, 0)), generator.Tile.ENEMY)

    def test_enemy_won(self):
        state = generator.LevelState(width=4, height=4, exit_pos=(0, -1))
        state.set_tile((1, 1), generator.Tile.PLAYER)
        state.set_tile((0, 0), generator.Tile.ENEMY)
        new_state = generator.LevelState(state=state, move=generator.Move.UP)
        self.assertEqual(new_state.outcome, generator.MoveOutcome.ENEMY_WON)

if (__name__ == '__main__'):
    unittest.main()
