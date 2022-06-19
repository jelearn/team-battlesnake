"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""

import itertools
import json
import random

from pprint import pprint
from typing import List

from astar import find_path
from models import Point, Move, Snake, Board, HeatMap

# From trial and error, checking more than 12 moves takes more than 1 second to compute
ASTAR_MOVE_LIMIT = 12


class Game:
    def __init__(
        self, data,
    ):
        self._num_opponents = len(data["board"]["snakes"]) - 1
        self._my_id = data["you"]["id"]
        self.game_id = data["game"]["id"]
        self.turn = int(data["turn"])
        self.shout_words = [
            "Work it",
            "Make it",
            "Do it",
            "Makes us",
            "Harder",
            "Better",
            "Faster",
            "Stronger",
        ]

    def shout(self):
        shout_pos = self.turn % len(self.shout_words)
        return self.shout_words[shout_pos]

    @property
    def num_opponents(self):
        return self._num_opponents

    @property
    def my_id(self):
        return self._my_id

    def start(self, data):
        board = Board.parse(data)
        print(
            "Playing a game with:\n"
            + "\n".join(" - {}".format(s.name) for s in board.snakes)
        )

    def move(self, data):
        board = Board.parse(data)

        possible_moves = list(board.valid_snake_moves(board.me))

        # print(f"{board}", "\nScore: {}".format(self.score(board)))
        print(json.dumps(data))

        # Start of snake choosing best move
        print(f"Possible Moves: {possible_moves}")
        print(f"Me: {board.me}")
        print(f"Others ({len(board.others)}): {board.others}")
        print(f"Food ({len(board.food)}): {board.food}")

        if not board.others:
            # TODO: favor being in middle of map.
            starve_threshold = max(
                board.me.size, int((board.size.x + board.size.y) / 4)
            )

            add_chase_tail_defense(board, force=True)

            if board.me.tail in Move.all_move_points(board.me.head):
                board.heat.add(board.me.tail, HeatMap.HEAT_CHASE_TAIL)

            if board.me.health > starve_threshold:

                for food in board.food:
                    board.heat.add(food, HeatMap.HEAT_SOLO_FOOD_DANGER)

            for next_point in possible_moves:
                # print(f"Check move: {next_point}")

                if next_point in board.food:
                    add_heat_when_starving(
                        next_point, board, starving_health=starve_threshold
                    )

                add_dead_end_heat(
                    next_point, board.me, board,
                )

        else:
            add_default_board_heat(board)

            add_forward_heat(board, possible_moves)

            move_counts = []

            for next_point in possible_moves:
                print(f"Check move: {next_point}")

                if next_point in board.food:
                    add_heat_when_starving(next_point, board)

                # my_future = board.me.move_toward(next_point, next_point in board.food)

                max_future_move_cnt = add_dead_end_heat(next_point, board.me, board)

                move_counts.append((next_point, max_future_move_cnt))

            if move_counts:
                add_move_count_heat(move_counts, board)

            if possible_moves:
                add_heat_for_self_distance(possible_moves, board)

                # Check to see if we're closer to weaker snakes, unless there's only one.
                roughly_third_board = int((board.size.x * board.size.y) / 3) + 1
                weaker_snake_range = (
                    roughly_third_board
                    if len(board.others) == 1
                    else min(board.size.x, board.size.y)
                )
                weakest_snakes = find_paths_from_snakes(
                    snakes=board.weaker_snakes(board.me),
                    board=board,
                    max_moves=weaker_snake_range,
                    alternate_limit=3,
                )

                # Consider stronger snakes that are less than half the board (in moves) away
                stronger_snakes = find_paths_from_snakes(
                    snakes=board.stronger_snakes(board.me),
                    board=board,
                    max_moves=9,
                    alternate_limit=1,
                    move_snakes=True,
                )

                add_future_kill_heat(
                    possible_moves, board, stronger_snakes, weakest_snakes
                )

                # We are weak, we must avoid big snakes
                # or we're all middle of the pack
                if stronger_snakes or not weakest_snakes:
                    add_most_dangerous_move_heat(board, stronger_snakes)

                    add_chase_tail_defense(
                        board, sorted_stronger_snakes=stronger_snakes
                    )

                    food_paths = find_paths_to_food(
                        board, max_moves=7, alternate_limit=0
                    )

                    add_extra_food_heat(food_paths, board, stronger_snakes)

                # TODO: Create a verbose mode option to have this printed.
                # print("Heat Map: ")
                # pprint(board.heat.map)

        if not possible_moves:
            possible_moves = [random.choice(Move.all_move_points(board.me.head))]
            print(f"Ahhhh! : {possible_moves}")

        # Sort the best moves first (according to "goodness heat")
        preferred_moves = sorted(
            possible_moves, key=lambda point: board.heat.goodness(point), reverse=True,
        )

        print(f"Preferred Moves:")
        for move in preferred_moves:
            if move in board.heat.map:
                print(
                    "  {0} ({1}): {2} => {3}".format(
                        move,
                        board.me.get_move_name(move),
                        board.heat.goodness(move),
                        board.heat.map[move],
                    )
                )
            else:
                print(
                    "  {0} ({1}): {2}".format(
                        move, board.me.get_move_name(move), board.heat.goodness(move),
                    )
                )

        move_point = preferred_moves[0]
        print(f"Choosing the highest ranked: {move_point}")

        move_name = board.me.get_move_name(move_point)

        next_shout = self.shout()
        print(f"MOVE {self.turn}: {move_name} ({move_point}) shouted: {next_shout}")
        return {"move": move_name, "shout": next_shout}

    def end(self, data):
        if any(s["id"] == self.my_id for s in data["board"]["snakes"]):
            print("{:!^50}".format("WINNER"))
        else:
            print("{:.^50}".format("Loser"))
        print("ending state:")
        pprint(data)
        final_board = Board.parse(data)
        print(final_board, "\nScore: {}".format(self.score(final_board)))

        return "ok"

    def score(self, board: Board):
        score = 0
        # dead snake = bad
        if not board.me:
            score = -50
        # long snake = good
        else:
            score += len(board.me) * 2

            # TODO: This is inaccurate in the sense that we don't really
            #   know if we killed them, just they are not there anymore.
            # 5 points per snake killed
            score += (self.num_opponents - len(board.others)) * 5

        return score


def find_paths_to_food(board: Board, max_moves: int = 7, alternate_limit: int = 3):
    return [
        (snake, path)
        for snake, path in [
            (
                food,
                find_path(
                    board.me,
                    food,
                    board,
                    max_moves=max_moves,
                    alternate_limit=alternate_limit,
                ),
            )
            for food in board.food
        ]
        if path
    ]


def find_paths_from_snakes(
    snakes: List[Snake],
    board: Board,
    max_moves: int = 7,
    alternate_limit: int = 0,
    move_snakes: bool = False,
):
    print(f"Find path in < {max_moves} from each {snakes} to {board.me}")

    paths_to_snake = [
        (snake, path)
        for snake, path in [
            (
                snake,
                find_path(
                    snake,
                    board.me.head,
                    board,
                    max_moves=max_moves,
                    alternate_limit=alternate_limit,
                    move_snake=move_snakes,
                ),
            )
            for snake in snakes
        ]
        if path
    ]

    return sorted(paths_to_snake, key=lambda x: len(x[1]))


def add_forward_heat(board: Board, possible_moves: List[Point]):
    """
    In general, moving in a straight line leaves open space for
    backup moves when threatened...
    :param board: The board, the forward heat will be given to the player ("me") snake.
    :param possible_moves: The currently calculated possible moves for the snake.
    """
    direction = board.me.get_direction()

    if not direction:
        return

    direction_point = board.me.head + direction
    if direction_point in possible_moves:
        board.heat.add(direction_point, HeatMap.HEAT_FORWARD)


def sort_by_distance(origin: Point, sortable: List[Point]) -> List[Point]:
    return sorted(sortable, key=lambda point: origin.distance(point))


def sort_move_points_by_distance(
    move_options: List[Point], destination_options: List[Point]
):
    """
    Sorts the `move_options` according to how far they are from the closest
    `destination_options` (closest to farthest) and sorts the destinations by distance from the origin.
    :param move_options:
    :param destination_options:
    :return: A sorted list of `move_options` to the closest destination.
    """

    # TODO: Revisit if this is too specialized to be worth keeping in a method.
    if not destination_options:
        return move_options

    move_dist = {}
    for move in move_options:
        move_dist[move] = sum(
            [move.distance(dest) for dest in destination_options]
        ) / len(destination_options)

    return sorted(move_options, key=lambda sort_move: move_dist[sort_move])


def sort_move_points_by_distance_enriched(
    move_options: List[Point], destination_options: List[Point]
):
    """
    Sorts the `move_options` according to how far they are from the closest
    `destination_options` (closest to farthest) and sorts the destinations by distance from the origin.
    :param move_options:
    :param destination_options:
    :return: A sorted list of tuples for "move" and it's average distance
        to the destinations.
    """

    # TODO: Revisit if this is too specialized to be worth keeping in a method.
    if not destination_options:
        return [(move, 0) for move in move_options]

    def point_distance(point: Point):
        return sum([point.distance(dest) for dest in destination_options]) / len(
            destination_options
        )

    return sorted(
        [(move, point_distance(move)) for move in move_options],
        key=lambda move_tuple: move_tuple[1],
    )


def sort_by_head_distance(reference: Point, sortable: List[Snake]) -> List[Snake]:
    return sorted(sortable, key=lambda snake: reference.distance(snake.head))


def sort_by_size(sortable: List[Snake]) -> List[Snake]:
    return sorted(sortable, key=lambda snake: snake.size)


def add_dead_end_heat(
    move: Point, snake: Snake, board: Board, add_heat: bool = True,
) -> int:

    moves_to_end = find_path(
        snake=snake.move_toward(move),
        goal=snake.tail,
        board=board,
        max_moves=min(snake.size + 2, board.size.x + board.size.y, ASTAR_MOVE_LIMIT),
        move_snake=False,
        return_closest=True,
    )

    # print("Moves to tail: ", moves_to_end)

    could_be_blocked = False
    moving_snake = snake
    for pos, path_move in enumerate(moves_to_end):
        moving_snake = moving_snake.move_toward(path_move)
        # print("Moving snake: ", moving_snake)

        if pos > 1 and board.heat.has_heat(path_move, HeatMap.HEAT_SNAKEFUTURE_MARKER):
            # print("Could be blocked at: ", path_move)
            could_be_blocked = True
            break

        elif len(list(board.valid_snake_moves(moving_snake))) > 1:
            # print("Multiple options at: ", path_move, " Moves: ", list(board.valid_snake_moves(moving_snake)))
            break

    if (
        # If there are no moves at all, it's a dead-end
        not moves_to_end
        # If we can't reach our size, there's a good chance we can't fit.
        # TODO:  There's a chance we might eat food, this should be accounted for.
        or (len(moves_to_end) <= snake.size and moves_to_end[-1] != snake.tail)
        # If there's a chance we'll get blocked off by another snake (stronger or weaker)
        # after this move, then we would be blocked in.
        or (len(moves_to_end) > 3 and could_be_blocked)
    ) and add_heat:
        board.heat.add(move, HeatMap.HEAT_DEADEND)

    return len(moves_to_end)


def is_closest_strongest_snake(
    target: Point,
    check_snake: Snake,
    board: Board,
    max_competition: int = -1,
    min_buffer: int = 3,
    check_snake_path: List[Point] = None,
    max_opponent_moves=7,
) -> bool:
    # -1 indicates we'll compete for the target regardless of how many WEAKER people are closer
    # Excluding yourself.

    other_snakes = [snake for snake in board.snakes if snake != check_snake]

    if not other_snakes:
        # Really?  Is this even possible?
        return True

    if max_competition == -1:
        max_competition = len(other_snakes)

    if not check_snake_path:
        check_snake_path = find_path(
            check_snake, target, max_moves=max_opponent_moves, board=board
        )

    if not check_snake_path:
        # If the snake has no path to the target, then it's clearly not the closest.
        return False

    closest_snakes = sorted(
        [
            (snake, path)
            for snake, path in [
                (
                    snake,
                    find_path(
                        snake=snake, goal=target, board=board, max_moves=min_buffer,
                    ),
                )
                for snake in other_snakes
            ]
            if path
        ]
        + [(check_snake, check_snake_path)],
        key=lambda x: len(x[1]),
    )

    check_rank = [
        pos
        for pos, snake in [
            (pos, snake) for pos, (snake, _) in enumerate(closest_snakes)
        ]
        if snake == check_snake
    ][0]

    # print(
    #     f"Is {check_snake} closest to {target} with rank {check_rank} of {closest_snakes}?"
    # )

    if len(closest_snakes) == 1:
        return True

    # We'll accept competition to a maximum number of competitors, as long as we're still stronger and they are
    # far enough away.
    elif check_snake != closest_snakes[0][0] and check_rank <= max_competition:

        is_closest = all(
            other_snake.size < check_snake.size
            or (
                other_snake.size > check_snake.size
                and len(check_snake_path) + min_buffer < len(other_path)
            )
            for other_snake, other_path in closest_snakes[0:check_rank]
        )

        # print("Is closest when not first: ", is_closest)

        return is_closest

    # Only go towards the destination if we're the closest AND we are stronger
    elif check_snake == closest_snakes[0][0]:
        is_closest = (
            # And not equidistant with the next closest (we should avoid collisions)
            len(check_snake_path) < len(closest_snakes[1][1])
            and (
                # And if we are we're also the stronger than them (make sure we can win)
                check_snake.size > closest_snakes[1][0].size
                # If we are just close enough block away, do it.
                # NOTE: Path length includes head and destination
                or len(check_snake_path) <= 5
            )
        )

        # print("Is closest when first: ", is_closest)

        return is_closest

    else:
        return False


def add_most_dangerous_move_heat(board: Board, sorted_stronger_snakes: List[tuple]):
    print("Stronger snakes to check for threat: ", sorted_stronger_snakes)
    possible_moves = list(board.valid_snake_moves(board.me))
    print("Possible dangerous moves: ", possible_moves)

    # If there are no snakes close enough to use, just exit.
    if not sorted_stronger_snakes or not possible_moves:
        return

    # print("Danger Sorted: ", sorted_stronger_snakes)

    for pos, (snake, path) in enumerate(sorted_stronger_snakes):
        # Only be afraid of the closest 2 snakes
        # TODO: Should we ignore snakes that are far away?
        if pos >= 2:
            break

        # print("Adding danger for: ", snake, " with path ", path)

        top_dangerous_move = sorted(
            possible_moves, key=lambda x: x.distance(snake.head)
        )[0]

        if board.on_edge(board.me.head):
            if top_dangerous_move in path:
                board.heat.add(top_dangerous_move, HeatMap.HEAT_STRONGER_SNAKE)
            else:
                board.heat.add(path[-2], HeatMap.HEAT_STRONGER_SNAKE)

            for off_edge_move in possible_moves:
                if not board.on_edge(off_edge_move):
                    board.heat.add(off_edge_move, HeatMap.HEAT_MOVE_OFF_EDGE)

        # If there is food at this move, and we'll grow to be as strong
        # as the others, just eat it!.
        elif top_dangerous_move in board.food and board.me.size + 1 >= snake.size:
            board.heat.add(top_dangerous_move, HeatMap.HEAT_FOOD_WHEN_WEAK)

        # Add dangerous heat if getting food doesn't bring us to at par with others
        else:
            # print("Adding stronger snake heat at: ", top_dangerous_move)
            board.heat.add(top_dangerous_move, HeatMap.HEAT_STRONGER_SNAKE)


def add_heat_when_starving(next_point: Point, board: Board, starving_health: int = 25):
    if board.me.health <= starving_health:
        board.heat.add(next_point, HeatMap.HEAT_FOOD_STARVING)


def add_heat_for_self_distance(possible_moves: List[Point], board: Board):
    """
    Ideally it's better not to be close to one-self, unless needed.
    When we're already on the edge, there is no bonus for this.
    """
    if board.me.size > 2:
        # if not board.on_edge(board.me.head):
        farthest_from_self = sorted(
            possible_moves,
            # TODO: Giving space for yourself is often good to make sure you have options
            #  Calculating it generically needs work.
            key=lambda point: min(
                point.distance(body_point) for body_point in board.me.body
            ),
            # key=lambda point: sum(
            #     point.distance(body_point) for body_point in board.me.body
            # )/len(board.me.body),
        )

        board.heat.add(farthest_from_self[-1], HeatMap.HEAT_FARTHEST_FROM_SELF)


def add_future_kill_heat(
    possible_moves: List[Point],
    board: Board,
    sorted_stronger_snakes: List[tuple],
    sorted_weakest_snakes: List[tuple],
):
    print("Checking weaker snakes for kill: ", sorted_weakest_snakes)
    print(
        "Consider stronger snakes to kill or abort attack on weaker: ",
        sorted_stronger_snakes,
    )

    # Identify some blocking moves against a stronger snake, but only if we have more than
    # one option.
    if board.others and len(possible_moves) > 1:
        snake_bodies = itertools.chain.from_iterable(
            [snake.body for snake in board.others]
        )
        candidate_blocks = [
            move
            for move, next_possible_moves in [
                (
                    move,
                    list(
                        board.valid_snake_moves(
                            board.me.move_toward(move, grow=(move in board.food))
                        )
                    ),
                )
                for move in possible_moves
                if (
                    board.on_edge(move)
                    or only_one(
                        next_move in snake_bodies
                        for next_move in Move.all_move_points(move)
                    )
                )
            ]
            if len(next_possible_moves) == 2
            and Move.are_opposite(move, next_possible_moves[0], next_possible_moves[1])
        ]

        print("Candidate blocking moves: ", candidate_blocks)

        if candidate_blocks:
            all_snakes_sorted = sorted(
                sorted_stronger_snakes + sorted_weakest_snakes, key=lambda x: len(x[1])
            )
            for pos, (snake, path) in enumerate(all_snakes_sorted):
                # Only do this for the closest 2 snakes
                if pos >= 2:
                    break

                # Do not do this if they are in killing distance or if they are
                # too far away.
                # TODO: Considering how many moves they have or how much open space
                #   there is would be really good to add.
                elif (
                    len(path) < 3
                    or len(path) > 7
                    and len(list(board.valid_snake_moves(snake.move_toward(path[1]))))
                    != 1
                ):
                    break

                block_move = sorted(
                    candidate_blocks, key=lambda x: x.distance(snake.head)
                )[0]

                # This final check makes sure we're not blocking in an opposite
                # direction from where the other snake is coming from.
                if board.me.head.distance(snake.head) > block_move.distance(snake.head):
                    print(f"Open space block move kill at {block_move} of {snake}")
                    board.heat.add(block_move, HeatMap.HEAT_SNAKEFUTURE_KILL_BLOCK)

    if sorted_weakest_snakes:
        # If we're the strongest outright
        if len(board.weaker_snakes(board.me)) == len(board.others):
            print("We are the strongest snake, being more agressive...")
            for weak_rank, (snake, path) in enumerate(sorted_weakest_snakes):
                weak_kill_move = path[-2]

                if weak_rank == 0:
                    board.heat.add(
                        weak_kill_move, HeatMap.HEAT_SNAKEFUTURE_KILL_CLOSEST
                    )

                # To avoid wasting time, we only check a fixed number of weaker snakes
                elif weak_rank >= 2:
                    break

                # If there is a path, and the next move is a kill, don't
                # add more heat because it's already counted as a possible kill.
                if len(path) > 2:
                    board.heat.add(weak_kill_move, HeatMap.HEAT_SNAKEFUTURE_KILL)

        # If we are not the strongest
        elif sorted_stronger_snakes:
            # Decide if we want to attack a weaker snake when we're not the strongest
            for weak_rank, (snake, path) in enumerate(sorted_weakest_snakes):
                # To avoid wasting time, we only check a fixed number of weaker snakes
                if weak_rank >= 1:
                    break

                # If there is a path, and the next move is a kill, don't
                # add more heat because it's already counted as a possible kill.
                weak_kill_move = path[-2]

                abort_kill = False
                for strong_rank, (strong_snake, strong_path) in enumerate(
                    sorted_stronger_snakes
                ):
                    # If there are less than 3 moves (excluding their head and mine)
                    # add danger
                    if len(strong_path) <= 5:
                        board.heat.add(weak_kill_move, HeatMap.HEAT_STRONGER_SNAKE)
                        abort_kill = True

                if not abort_kill:
                    board.heat.add(weak_kill_move, HeatMap.HEAT_SNAKEFUTURE_KILL)


def only_one(booleans) -> bool:
    """
    :param booleans: A list of truthy objects to test.
    :return: True if only one of the list evaluates to True, False otherwise.
    """
    return len(list(truthy for truthy in booleans if truthy)) == 1


def add_move_count_heat(move_counts: List[tuple], board: Board):
    # If there's only one move, don't give it a bonus.
    if len(move_counts) == 1:
        return

    sorted_moves = sorted(
        [
            # Sort by the move with the most next immediate moves
            (move, len(list(board.valid_snake_moves(board.me.move_toward(move)))),)
            for move, count in move_counts
        ],
        key=lambda item: item[1],
        reverse=True,
    )

    for pos, move in enumerate(sorted_moves):
        # If the first and 2nd moves are the same, then don't count them as higher
        # than the other
        if pos == 0 and sorted_moves[0][1] > sorted_moves[1][1]:
            board.heat.add(move[0], HeatMap.HEAT_MOST_FUTURE)
        elif pos == 0 or pos == 1:
            board.heat.add(move[0], HeatMap.HEAT_MOST_FUTURE_2ND)
        elif move[1] == 1:
            board.heat.add(move[0], HeatMap.HEAT_LEAST_FUTURE)


def add_default_board_heat(board: Board):
    my_valid_moves = list(board.valid_snake_moves(board.me))
    for snake in board.snakes:
        for body in snake.body:
            board.heat.add(body, HeatMap.HEAT_SNAKEBODY)

        if snake != board.me:
            for move in board.valid_snake_moves(snake):
                board.heat.add(move, HeatMap.HEAT_SNAKEFUTURE_MARKER)

                if snake.size >= board.me.size:
                    board.heat.add(move, HeatMap.HEAT_SNAKEFUTURE_DEATH)
                    board.heat.add(move, HeatMap.HEAT_SNAKEFUTURE_STRONG_MARKER)

                elif move in my_valid_moves:
                    # i.e. the this turn we could kill this snake
                    board.heat.add(move, HeatMap.HEAT_POSSIBLE_KILL)

    for food in board.food:
        board.heat.add(food, HeatMap.HEAT_FOOD)

        # Food on the edge is more dangerous
        if board.on_edge(food):
            board.heat.add(food, HeatMap.HEAT_FOOD_EDGE)

        # More value should be added when there are multiple food next to one another.
        # Also, if food is on the edge it should be considered dangerous.
        for neighbor in Move.all_move_points(food):
            if neighbor in board.food:
                board.heat.add(food, HeatMap.HEAT_FOOD_CLUSTER)

    bottom_left_corner = Point(0, 0)

    # The corners are dangerous
    board.heat.add(bottom_left_corner, HeatMap.HEAT_BOARD_CORNER)
    board.heat.add(
        Point(bottom_left_corner.x, board.size.y - 1), HeatMap.HEAT_BOARD_CORNER
    )
    board.heat.add(
        Point(board.size.x - 1, bottom_left_corner.y), HeatMap.HEAT_BOARD_CORNER
    )
    board.heat.add(Point(board.size.x - 1, board.size.y - 1), HeatMap.HEAT_BOARD_CORNER)

    # The edges are somewhat dangerous
    for vertical in range(bottom_left_corner.y, board.size.y):
        board.heat.add(Point(board.size.x - 1, vertical), HeatMap.HEAT_BOARD_EDGE)
        board.heat.add(Point(bottom_left_corner.x, vertical), HeatMap.HEAT_BOARD_EDGE)

    for horizontal in range(bottom_left_corner.x, board.size.x):
        board.heat.add(Point(horizontal, board.size.y - 1), HeatMap.HEAT_BOARD_EDGE)
        board.heat.add(Point(horizontal, bottom_left_corner.y), HeatMap.HEAT_BOARD_EDGE)

    # The out of bounds is death are somewhat dangerous (this is probably overkill..)
    for vertical in range(bottom_left_corner.y - 1, board.size.y + 1):
        board.heat.add(
            Point(bottom_left_corner.x - 1, vertical), HeatMap.HEAT_BOARD_OUTSIDE
        )

    for horizontal in range(bottom_left_corner.x - 1, board.size.x + 1):
        board.heat.add(
            Point(horizontal, bottom_left_corner.y - 1), HeatMap.HEAT_BOARD_OUTSIDE
        )


def add_chase_tail_defense(
    board: Board, force: bool = False, sorted_stronger_snakes: List[tuple] = None
):
    tail_path = find_path(
        snake=board.me,
        goal=board.me.tail,
        board=board,
        move_snake=True,
        alternate_limit=1,
        max_moves=board.me.size + 1,
    )

    # Only proceed if there is a path to the tail, and the next move isn't a collision with the tail.
    if tail_path and tail_path[1] != board.me.tail:
        tail_move = tail_path[1]

        # print(f"Chase Tail: move {tail_move} in Stronger Paths: ", stronger_paths)

        if sorted_stronger_snakes:
            stronger_paths = list(
                itertools.chain.from_iterable(
                    path
                    for _, path in sorted_stronger_snakes
                    if len(path) <= len(tail_path) + 3
                )
            )

            if tail_move in stronger_paths:
                return

        if not board.food:
            board.heat.add(tail_move, HeatMap.HEAT_CHASE_TAIL)

        # If we're in a 1 on 1 battle, and we're weak, chase tail.
        elif (
            len(board.others) == 1
            and board.me.size < board.others[0].size
            and 2 <= board.me.head.distance(board.others[0].head) <= 5
        ):
            board.heat.add(tail_move, HeatMap.HEAT_CHASE_TAIL_URGENT)

        elif force:
            board.heat.add(tail_move, HeatMap.HEAT_CHASE_TAIL_URGENT)


def add_extra_food_heat(food_paths: tuple, board: Board, sorted_stronger_snakes: tuple):

    # don't bother adding heat if there is no food or a stronger snake
    # is too close
    if not food_paths or (
        sorted_stronger_snakes and len(sorted_stronger_snakes[0][1]) <= 5
    ):
        return

    closest_food = sorted(food_paths, key=lambda x: len(x[1]))

    # Only consider stronger snakes within a specific distance
    stronger_paths = (
        []
        if not sorted_stronger_snakes
        else itertools.chain.from_iterable(
            path for _, path in sorted_stronger_snakes if len(path) <= 5
        )
    )

    print("Check food: ", closest_food)

    food_chosen = 0
    for pos, (food, path) in enumerate(closest_food):
        move_towards_food = path[1]

        # For now, only choose one or if the closest is too far away
        # when we're weak and on a stronger snakes path to us.
        if food_chosen > 1 or (
            len(path) >= 5
            and sorted_stronger_snakes
            and move_towards_food in stronger_paths
        ):
            break

        if sorted_stronger_snakes and move_towards_food not in stronger_paths:
            add_heat_when_starving(move_towards_food, board)

        # Make sure we're the closest, strongest, snake (max 1 competitor)
        is_closest = is_closest_strongest_snake(
            target=food,
            check_snake=board.me,
            board=board,
            max_competition=1,
            check_snake_path=path,
            max_opponent_moves=5,
        )

        print(f"Is {board.me.head} closest ({is_closest}) to {food} of: {board.others}")
        if is_closest:
            food_chosen += 1
            print(f"Adding good heat for food: {move_towards_food}")
            board.heat.add(move_towards_food, HeatMap.HEAT_FUTURE_FOOD)

            if sorted_stronger_snakes and move_towards_food not in stronger_paths:
                board.heat.add(move_towards_food, HeatMap.HEAT_FOOD_WHEN_WEAK)

        # If we're not the strongest and closest, treat that point as dangerous
        # Negates the default goodness of food.
        else:
            board.heat.add(move_towards_food, HeatMap.HEAT_FUTURE_FOOD_FIGHT)
