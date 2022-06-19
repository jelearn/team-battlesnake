import math

from enum import Enum
from typing import List, Set


class Point:
    __slots__ = "x", "y"
    """
    Represents a point on a BattleSnake game board.
    The point may be on the board or not, depending on the board size.
    """

    def __init__(self, x, y):
        """
        Keyword arguments:
        x -- horizontal position
        y -- vertical position
        """
        self.x = int(x)
        self.y = int(y)

    def __eq__(self, p):
        # Point(1,1) == Point(1,1)
        return self.x == p.x and self.y == p.y

    def __str__(self):
        return f"({self.x},{self.y})"

    def __repr__(self):
        return f"Point({self.x},{self.y})"

    def __add__(self, p):
        return Point(x=self.x + p.x, y=self.y + p.y)

    def __hash__(self):
        return hash(self.__repr__())

    def in_bounds(self, board_size):
        """
        Return if this point is on the board based the `board_size` point
        representing the outer boundary (i.e. out of bounds) of the game board.

        Keyword arguments:
        board_size -- The outer boundary of the board as a Point, e.g. 11x11 = Point(11,11)
        """
        return 0 <= self.x < board_size.x and 0 <= self.y < board_size.y

    def distance(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)


class HeatType(Enum):
    # The values represent escalation of goodness, but then danger.
    # Their value order represents priority of which should be treated as more important (i.e. life over death)
    NONE = 0
    GOOD = 1
    DANGER = 2
    POSSIBLE_DEATH = 3
    DEATH = 4


class Heat(object):
    def __init__(self, name: str, type: HeatType = HeatType.DANGER, value: int = 1):
        self.name = name
        self.value = value
        self.type = type

    def __repr__(self):
        return f"Heat(name='{self.name}', value={self.value}, type={self.type})"

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.type == other.type
            and self.value == other.value
        )

    def __hash__(self):
        return hash(f"{self.name}{self.type}{self.value}")


class HeatMap(object):
    DEATH_HEAT = 100000 * -1
    DEATH_HEAT_NAME = "death"

    DANGER_TYPES = [HeatType.DANGER, HeatType.POSSIBLE_DEATH]
    DEATH_TYPES = [HeatType.DEATH, HeatType.POSSIBLE_DEATH]

    HEAT_EMPTY = Heat("empty", type=HeatType.NONE, value=0)

    # This is intended as a tiebreaker and in general favor straight lines
    # which leave space for backup moves.
    HEAT_FORWARD = Heat("forward", type=HeatType.GOOD, value=1)

    HEAT_MOST_FUTURE = Heat("most_future", type=HeatType.GOOD, value=3,)
    HEAT_MOST_FUTURE_2ND = Heat("2nd_most_future", type=HeatType.GOOD, value=1,)
    HEAT_LEAST_FUTURE = Heat("least_future", type=HeatType.DANGER, value=3,)

    HEAT_FOOD = Heat("food", type=HeatType.GOOD, value=HEAT_MOST_FUTURE_2ND.value + 3)

    HEAT_FOOD_EDGE = Heat("food-edge", type=HeatType.DANGER, value=1)

    HEAT_FOOD_CLUSTER = Heat(
        "food-cluster",
        type=HeatType.GOOD,
        value=HEAT_FOOD.value + HEAT_FORWARD.value + 5,
    )
    HEAT_FOOD_STARVING = Heat(
        "food_starving", type=HeatType.GOOD, value=HEAT_FOOD.value + 4
    )
    HEAT_FUTURE_FOOD_FIGHT = Heat(
        "food-fight", type=HeatType.DANGER, value=HEAT_FOOD.value + 2
    )
    HEAT_FUTURE_FOOD = Heat(
        "future-food", type=HeatType.GOOD, value=HEAT_MOST_FUTURE.value + 2
    )

    HEAT_FARTHEST_FROM_SELF = Heat(
        "farthest_from_self", type=HeatType.GOOD, value=HEAT_MOST_FUTURE_2ND.value + 1,
    )

    HEAT_CHASE_TAIL = Heat(
        "chase_tail", type=HeatType.GOOD, value=HEAT_MOST_FUTURE_2ND.value + 1
    )
    HEAT_CHASE_TAIL_URGENT = Heat(
        "chase_tail_urgent", type=HeatType.GOOD, value=HEAT_CHASE_TAIL.value + 2
    )

    HEAT_FOOD_WHEN_WEAK = Heat("food-when-weak", type=HeatType.GOOD, value=7)

    # This is simply used to mark a possible future move of a snake.
    HEAT_SNAKEFUTURE_MARKER = Heat("future-snake-marker", type=HeatType.NONE, value=0)
    HEAT_SNAKEFUTURE_STRONG_MARKER = Heat(
        "future-strong-snake-marker", type=HeatType.NONE, value=0
    )

    HEAT_POSSIBLE_KILL = Heat("possible_kill", type=HeatType.GOOD, value=9)
    HEAT_SNAKEFUTURE_KILL = Heat("future-kill", type=HeatType.GOOD, value=2)
    HEAT_SNAKEFUTURE_KILL_CLOSEST = Heat(
        "future-kill-closest", type=HeatType.GOOD, value=2
    )

    HEAT_BOARD_EDGE = Heat("edge", type=HeatType.DANGER, value=5 + HEAT_FORWARD.value)
    HEAT_MOVE_OFF_EDGE = Heat(
        "move-off-edge", type=HeatType.GOOD, value=HEAT_FORWARD.value + 3
    )
    HEAT_BOARD_CORNER = Heat(
        "corner",
        type=HeatType.DANGER,
        # TODO: Avoiding the corner is covered by avoiding the edge...
        value=0,
    )

    HEAT_SNAKEFUTURE_KILL_EDGE = Heat(
        "future-kill-edge",
        type=HeatType.GOOD,
        value=HEAT_BOARD_EDGE.value + HEAT_MOST_FUTURE.value + HEAT_FORWARD.value + 2,
    )

    HEAT_SNAKEFUTURE_KILL_BLOCK = Heat(
        "future-kill-block", type=HeatType.GOOD, value=HEAT_SNAKEFUTURE_KILL_EDGE.value,
    )

    HEAT_SNAKEBODY = Heat("snake-body", type=HeatType.DEATH)
    HEAT_SNAKEFUTURE_DEATH = Heat(
        "snake-future-death", type=HeatType.POSSIBLE_DEATH, value=16,
    )
    HEAT_SOLO_FOOD_DANGER = Heat(
        "solo-food-death", type=HeatType.DANGER, value=HEAT_SNAKEFUTURE_DEATH.value - 1,
    )

    HEAT_STRONGER_SNAKE = Heat("stronger-snake", type=HeatType.DANGER, value=10)
    HEAT_STRONGER_SNAKE_EDGE = Heat(
        "stronger-snake-on-edge", type=HeatType.DANGER, value=2
    )

    HEAT_DEADEND_POTENTIAL = Heat("potential-deadend", type=HeatType.DANGER, value=3)
    HEAT_DEADEND = Heat("deadend", type=HeatType.DEATH)

    HEAT_BOARD_OUTSIDE = Heat("outofbounds", type=HeatType.DEATH)

    def __init__(self):
        self.map = {}

    def get(self, point: Point) -> Set[Heat]:
        return self.map[point] if point in self.map else set()

    def add(self, point: Point, heat: Heat):
        if point in self.map:
            self.map[point].add(heat)

        else:
            self.map[point] = {heat}

    def has_heat(self, point: Point, heat: Heat) -> bool:
        return point in self.map and heat in self.map[point]

    @staticmethod
    def total_goodness(heat: List[Heat]) -> int:
        # Assume nothing
        safety = 0
        for heat_point in heat:
            if heat_point.type == HeatType.DEATH:
                return HeatMap.DEATH_HEAT
            elif heat_point.type in HeatMap.DANGER_TYPES:
                safety -= heat_point.value
            else:
                safety += heat_point.value

        return safety

    def goodness(self, point: Point) -> int:
        if point not in self.map:
            # If point is not recorded, assume basic-empty safety
            return HeatMap.HEAT_EMPTY.value

        point_heat = self.map[point]

        if HeatType.DEATH in set(heat.type for heat in point_heat):
            return HeatMap.DEATH_HEAT

        return max(
            HeatMap.DEATH_HEAT,
            # Primarily based on overall goodness
            HeatMap.total_goodness(point_heat) * 1000
            # sum(1 for heat in self.get(point) if heat.type in [HeatType.GOOD]) * 1000
            # Overall number of DANGER items 1st tie breaker by REDUCING goodness
            + sum(1 for heat in self.get(point) if heat.type == HeatType.POSSIBLE_DEATH)
            * -100
            # Overall number of DANGER items 2st tie breaker by REDUCING goodness
            + sum(1 for heat in self.get(point) if heat.type == HeatType.DANGER) * -10
            # Lastly the overall number of good is the last tie breaker by INCREASING goodness
            + sum(1 for heat in self.get(point) if heat.type == HeatType.GOOD) * 1,
        )

    def __repr__(self):
        return f"HeatMap(map={self.map})"


class Move(Enum):
    """
    The logical board move related to the required adjustment relative to
    apply to another Point in order to move in that direction.
    """

    up = Point(0, 1)
    down = Point(0, -1)
    left = Point(-1, 0)
    right = Point(1, 0)

    @staticmethod
    def all_move_values() -> list:
        """
        Points referencing the relative difference of all moves, that would be applied to
        another point to calculate the new Point after that move.
        :return: Points to add to another Point for all possible moves.
        """
        return [move.value for move in Move.__members__.values()]

    @staticmethod
    def all_move_points(position: Point) -> list:
        """
        :param position: The Point of the starting position.
        :return: A list of all possible move Points from the given starting Point.
        """
        if not position:
            raise ValueError("Must specify a Point argument.")
        return [position + move_value for move_value in Move.all_move_values()]

    @staticmethod
    def get_move(from_point: Point, to_point: Point):
        if to_point.x > from_point.x:
            return Move.right
        elif to_point.x < from_point.x:
            return Move.left
        elif to_point.y > from_point.y:
            return Move.up
        elif to_point.y < from_point.y:
            return Move.down

        raise ValueError(
            f"Could not determine move from Point {from_point} to {to_point}"
        )

    @staticmethod
    def are_opposite(origin: Point, first_move: Point, second_move: Point):
        """
        :param origin: The point of reference for other moves
        :param first_move: An arbitrary choice.
        :param second_move: An alternate arbitrary choice.
        :return: True if the moves are in opposite directions, False otherwise.
        """
        if first_move == second_move:
            return False

        compare_moves = [
            Move.get_move(origin, first_move),
            Move.get_move(origin, second_move),
        ]

        return compare_moves in [[Move.up, Move.down], [Move.left, Move.right]]


class Snake:
    __slots__ = "id", "name", "health", "body", "head", "tail", "size"
    """
    Encapsulates a snake in the BattleSnake game:
        - The moves it can make.
        - It's attributes (body, head, tail).
        - Utilities for getting the logical "move" for the snake
          to get to another point.
    """

    def __init__(self, id: str, name: str, health: int, body: List[Point]):
        self.id = id
        self.name = name
        self.health = health
        # We assume the Points will be used in an immutable way.
        self.body = body[:]
        self.head = self.body[0]
        self.tail = self.body[-1]
        self.size = len(body)

    def __copy__(self):
        return self.__init__(self.id, self.name, self.health, self.body)

    def __eq__(self, other_snake):
        """
        For the purposes of this game, two snakes will be equal if they have the same ID, regardless of their body.
        :param other_snake: The snake being compared.
        :return: `True` if they are the same snake, `False` otherwise.
        """
        return self.id == other_snake.id

    def __contains__(self, p):
        return p in self.body

    def __len__(self):
        return len(self.body)

    def __repr__(self):
        return f"Snake('{self.id}', '{self.name}', {self.health}, {self.body})"

    def __hash__(self):
        return hash(self.id)

    def possible_moves(self):
        moves = []

        for m in Move.all_move_points(self.head):
            if m not in self or (
                # If the move is the tail, and we've fully spawn on the board
                # (i.e. size greater than 3) AND we haven't just eaten (i.e. health < 100)
                # then we can safely move into where our tail was.
                m == self.tail
                and self.size > 3
                and self.health < 100
            ):
                moves.append(m)

        return moves

    def move_toward(self, target_point: Point, grow: bool = False):
        """
        Creates a new Snake based on the current that moves toward the specified point (as best it can).
        :param target_point: The Board Point toward which the Snake should move.
        :param grow: Whether this movement should grow the snake.
        :return: A new Snake.
        """
        return self.move_direction(self.get_move_point(target_point), grow)

    def move_direction(self, move_direction: Point, grow: bool = False):
        """
        Creates a new Snake based on the current where it has moved in the `Move` Point direction indicated by the
        argument.
        The snakes health will decrease, unless it was told to grow in which case
        the health will be reset to 100.
        :param move_direction: One of the move direction points defined by `Move`.
        :param grow: Whether this movement should grow the snake.
        :return: A new snake.
        """
        if move_direction not in Move.all_move_values():
            # We fail hard here because otherwise passing the wrong arg would not result in a valid snake.
            raise ValueError(f"Invalid Move point direction: {move_direction}")

        if grow:
            body_base = self.body[:]
            new_health = 100
        else:
            body_base = self.body[:-1]
            new_health = self.health - 1

        # According to the docs, every move costs one health point
        return Snake(
            id=self.id,
            name=self.name,
            health=new_health,
            body=[self.head + move_direction] + body_base,
        )

    def get_direction(self):
        """
        Get's the "direction" in terms of Move where the snake is currently heading.
        :return: The move direction the snake is heading, unless it's length is 1 which will be None.
        """
        if len(self.body) == 1:
            return None
        return Move.get_move(self.body[1], self.body[0]).value

    def get_move_name(self, new_point: Point):
        return self.get_move(new_point).name

    def get_move_point(self, new_point: Point):
        """
        Gets `Move` point direction value for the Snakes head to the specified `new_point`.
        :param new_point:
        :return: A Point value relative to the given point (not an absolute point on a board).
        """
        return self.get_move(new_point).value

    def get_move(self, new_point: Point):
        return Move.get_move(self.head, new_point)


class Board:
    def __init__(
        self,
        *,
        game_id: str,
        my_id: str,
        size: Point,
        snakes: dict,
        food: List[Point],
        heat: HeatMap,
    ):
        self._game_id = game_id
        self._my_id = my_id
        self._size = size
        self._snakes = snakes
        self._food = food
        self._heat = heat

    @staticmethod
    def parse(data: dict):
        heat_map = HeatMap()

        game_id = data["game"]["id"]
        my_id = data["you"]["id"]
        snakes = {}
        for snake in data["board"]["snakes"]:
            body = [Point(**point) for point in snake["body"]]
            snake_id = snake["id"]
            snakes[snake_id] = Snake(
                id=snake_id, name=snake["name"], health=snake["health"], body=body
            )

        foods = [Point(**point) for point in data["board"]["food"]]

        board_size = Point(x=data["board"]["width"], y=data["board"]["height"])

        return Board(
            game_id=game_id,
            my_id=my_id,
            size=board_size,
            snakes=snakes,
            food=foods,
            heat=heat_map,
        )

    def valid_snake_moves(self, snake: Snake):
        """
        Returns moves that are in-bounds and not to itself, to other snakes.
        Otherwise return nothing.

        :param snake: The snake making the move.
        :return: A non-guaranteed death/disqualifying move.
        """
        for move in snake.possible_moves():
            if move.in_bounds(self.size):
                in_snake = False
                for other_snake in self.snakes:
                    # We do this check here, in order to test a
                    # artificial future snake into a board and still
                    # evaluate it's moves.
                    if other_snake != snake and move in other_snake.body:
                        in_snake = True
                        break

                if not in_snake:
                    yield move

    @property
    def me(self):
        return self._snakes.get(self._my_id, None)

    @property
    def snakes(self):
        return self._snakes.values()

    @property
    def food(self):
        return self._food

    @property
    def heat(self):
        return self._heat

    @property
    def others(self):
        return [s for _id, s in self._snakes.items() if _id != self._my_id]

    def weaker_snakes(self, snake: Snake) -> List[Snake]:
        return [
            other_snake for other_snake in self.snakes if other_snake.size < snake.size
        ]

    def stronger_snakes(self, snake: Snake) -> List[Snake]:
        return [
            other_snake for other_snake in self.snakes if other_snake.size > snake.size
        ]

    def on_edge(self, point: Point, size: int = 1) -> bool:
        max_boarder = int((self.size.x + self.size.y) / 2)
        if size > max_boarder:
            size = max_boarder
        for i in range(0, size):
            return (
                point.x == i
                or point.y == i
                or point.x == self.size.x - 1 - i
                or point.y == self.size.y - 1 - i
            )

    @property
    def size(self):
        return self._size

    def __str__(self):
        """Return an ASCII art representation of the board"""
        header = "╔" + "╤".join(["==="] * self.size.x) + "╗"
        spacer = "╟┄" + "┄┼┄".join(["┄"] * self.size.x) + "┄╢"
        footer = "╚" + "╧".join(["==="] * self.size.x) + "╝"

        lines = []
        for y in reversed(range(self.size.y)):
            line = []
            for x in range(self.size.x):
                p = Point(x, y)
                if p in self.food:
                    line.append("+")
                    continue
                for s in self.snakes:
                    if p in s:
                        if s.head == p:
                            line.append(s.name[0].upper())
                        else:
                            line.append(s.name[0].lower())
                        break
                else:
                    line.append(" ")
            lines.append("║ " + " │ ".join(line) + " ║")
        return "\n".join([header, ("\n" + spacer + "\n").join(lines), footer])
