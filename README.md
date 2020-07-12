# ShadeChange Level Generator

A Sunday project for generating levels for the [ShadeChange](https://itch.io/jam/my-first-game-jam-summer-2020/topic/867940/shadechange-a-game-where-you-need-to-change-colors-to-solve-a-puzzle) game. Enjoy!

## Installing

Just download the `generator.py` script and a Python 3 interpreter.

## Usage

Use python 3 to call `generator.py` like this:

    python3 generator.py

See all available options by calling:

    python3 generator.py --help

## Example with spiral

     White Field (1):
    ....
    ....
    ...#
    ....
     Black Field (0):
    .#..
    @...
    .#.p
    ....
     Outcome: MoveOutcome.UNDETERMINED
     Exit: (4,1)
     Moves: ←, ↓, →, ↑, ←, ⇄, →, ↓, →
     Start: (3, 2)


    0,0,1
    0,1,1
    0,2,1
    0,3,1
    1,0,1
    1,1,1
    1,2,1
    1,3,1
    2,0,1
    2,1,1
    2,2,1
    2,3,1
    3,0,1
    3,1,1
    3,2,2
    3,3,1

    0,0,1
    0,1,1
    0,2,1
    0,3,1
    1,0,1
    1,1,1
    1,2,1
    1,3,1
    2,0,1
    2,1,1
    2,2,1
    2,3,1
    3,0,1
    3,1,1
    3,2,2
    3,3,1

    3,2,0

    4,1
