# Team Battle Snake Project

Team battle snake project with the objective is to work on our Python and programming skills together on a common goal, and have fun.

This is essentialy a really old clone of the [Official Python starter-snake-python](https://github.com/battlesnakeofficial/starter-snake-python).

This copy is saved as reference of the team's work together during 2020-2021 while honing our programming skills.

## References:

See:
    - [Main Documentation](https://docs.battlesnake.com/)
    - [Python Starter Snake](https://github.com/battlesnakeofficial/starter-snake-python)

A lot of the documentation used to create this snake is obsolete and no longer
exists as it was created in 2021 before the explosion of new BattleSnake game features.

### Collaboration Snake

The snake logic is currently a procedural method of choosing safe moves, than detecting preferred safe moves based on
fixed criteria:

- Don't kill self, but kill other snake if opportunity arises. 
- If there food is there, eat it.
- Prefer moving toward food if there is not a closer stronger snake to that food.
- If longer than more half the snakes, attack the closest shorter snake.
- Panic.

## Utilities

The included `battlesnake_board_util.py` utility transforms a ASCII-art
representation of the game board (printed by the snake server) into the
BattleSnake game data JSON format.

This is used to tweak and create unit tests for specific scenarios that
are tested using `pytest`, which you can refer to in: [tests](./tests)

## Tasks

### Snake Logic TODO Ideas

- (X) Setup Server to accept and track multiple games start/finish/routing to the current game state (stubbed).
- (X) Initial dummy game snake choices where snake just does left right up down scan of arena (later logic to be filled in).

- (X) Update `server.py` to support custom port for multiple snakes on main server.
- (X) Discount move that would collide with self.
- (X) Discount out of bounds moves.
- (X) Discount other snakes possible moves and current position.
- (X) As a last resort, choose an opponent tail, or then a possible opponent choice.
- (X) Move toward food if possible next move.
- (X) Convert to use classes to model Snake and point and movement.
- (X) Go for food if possible.

- (X) Consider which routes are (or could be) dead-end, for example:
    - don't double back to one's self

- (X) Review and clean-up code, as per comments from peer review with Carey. (done in v1.4)
    - Pull in Game and Board classes from Carey's branch.
    - Review/implement Carey's comments in: [server.py](server.py)

- (X) Implement basic move scoring algorithm to apply when all choices seem equal (given our current logic). (done in v1.6)

- (X) Continue further transition to class-based implementation:
    - (X) Encapsulate move logic in snake to allow everyone to extend with their own logic?
    - (X) Refactor move logic into Game, as per Carey's implementation.
    - (X) Parameterize snake style?
    
- (X) Score the value of a move/Point (done in v1.6)
    - Count number of consecutive free squares (before reaching boundaries or other snakes).
    - Quantify tight spaces, make sure our body can fit in open spaces.
    - Only consider length of snake +1 steps in to future for those tight spaces.
    
- (X) Use score to rate future snake head positions + eating or not eating. 
    - don't go towards another snake's body loop
    
- (X) Use sets instead of lists. (done in v1.6)
    - Models now support use with sets.

- (.) Implement some team ideas:
        - Time component, look into the future. 
            - Assign value to future moves (Min/Max value)
            - Flood-fill/analyse moves adjacent positions.
        - Develop game value/score algorithm of a given move/Point.
        - Future Strategies?
            - Keep shorter, unless needed.
            - Just get as long as you can.
            - Early game vs. late game.
            - (X) target food until longer than some of the snakes, then attack the shorter snakes.

- (X) Write unit tests for classes. (done in v1.6)

- (X) Calculate closest food from a snake's head (arbitrary distance between points).
- (X) Detect if an opponent snake closer to the food than you when getting food.
    - (X) Evade or go for food (i.e. if there is danger going for food, should it?)
- (X) Calculate opponent snake direction. (done in v1.6)
- (X) Prototype different choice algorithms. (done in v1.6)
    - E.g. Heat map - Hans has started this in his snake.

- (X) Implement A\* algorithm (see [astar.py](astar.py))
- ( ) Machine Learning setup to learn/suggest best choices :)
- ( ) Setup basic server DoS/invalid request filtering.

- (X) Print snake move time in logs.
- (X) Create static reference test game(s) to run as unit tests, to verify the snake's decision time. (done in v1.6)
    - Each other snake's moves.
    - Run against current snake's algorithm.
    - Objective is to make sure we are well below 500 ms.

## Other Interesting Ingredients

The following is a list of all the nuances of the game that we've discussed so far:

- Our snake is in the list of "board" snakes, as well as under the "you" section.
- Head-to-head collisions, shorter snake loses, ties kill both.
- Head to body collisions, head snake lose.
- Disks make you longer and give you health, but each move decreases your health (not length).
- Server must respond in 500ms, otherwise previous move is used.
- Snake tail does not move until after the collision check, can't move into future free spot.
- Position notes: 
    - x = horizontal
    - y = vertical
    - Position (0,0) is the top left corner.
    - For a 11x11 board, the bottom right corner's position is (10,10)

## Other Snakes

Inital set from brainstorming session:

- `Slython`
- `VOS_power`
- `max-power-snake`
- `BayleeSnake 2: Electric Boogaloo`

Top *Public* snakes from [global arena](https://play.battlesnake.com/arena/global/):

- `Git Adder` & `Git Adder (2)`
- `Bookworm`
- `shielded-woodland`
- `YOUNGNASTY`
- `Jah-Snake`
