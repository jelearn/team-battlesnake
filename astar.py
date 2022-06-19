"""
This implementation of the A-Star algorithm is based on the tutorial:
https://www.simplifiedpython.net/a-star-algorithm-python-tutorial/

It's adapted for the Board, Snake, Point model of BattleSnake.
"""

import copy
import time

# PriorityQueue is a data structure. It organize items based on priority iset.
from queue import PriorityQueue
from typing import List

from models import Board, Snake, Point, Move


class State(object):
    __slots__ = "parent", "_children", "position", "dist", "start", "goal", "path"
    """
    This is the base class that is to be used to store all the important steps that are
    used for A* algorithm.
    """

    def __init__(self, position, parent, start=None, goal=None):
        self._children = []  # Children is a list of all possibilities
        self.parent = parent  # store current parent
        self.position = position  # store current value
        self.dist = 0  # store current distance, dist is not actually gonna be set
        # here, it is just a placeholder. It actually meant to be set to sub state
        # or subclasses of State class

        # Now Check the parent is plucked in
        # if the parent is plucked in do following
        if parent:
            self.start = parent.start  # store start state
            self.goal = parent.goal  # store goal state

            # copy the parent path to your path. [:] is actually
            # allows to make a copy of that list(self.path) into our own list.
            # if [:] will be not here then self.path will have same value as parent.path
            # That's why [:] is important.
            self.path = parent.path[:]

            # Store all values into our path. This path is basically
            # building own self and keeping track to where we at.
            self.path.append(position)

        # check for if there is no parent
        else:
            # set a path with list of objects started with our current value
            self.path = [position]
            self.start = start  # store start state
            self.goal = goal  # store goal state

    def distance(self):
        """
        :return: The distance between the state's current position and the goal.
        """
        pass

    def children(self) -> list:
        """
        :return: The move options available at this state, based on the current position and any other implementation
            details of the state implementation.
        """
        pass

    def __lt__(self, other):
        """
        A state is less than another based on the distance to the goal divided by the number of moves (i.e. path) made
        towards that goal.
        :param other: The other state being compared.
        :return: True if the state is closer than the `other` State, False otherwise.
        """
        return self.distance() / len(self.path) < other.distance() / len(other.path)


class StateSnake(State):
    __slots__ = "board", "snake"

    def __init__(
        self,
        position: Point,
        parent,
        board: Board,
        snake: Snake,
        start: Point = None,
        goal: Point = None,
    ):
        super(StateSnake, self).__init__(
            position=position, parent=parent, start=start, goal=goal
        )  # create constructor
        self.dist = self.distance()
        self.board = board
        self.snake = snake

    def distance(self):
        # first check to see if we have reached to our goal, and if we have then simply return 0
        if self.position == self.goal:
            return 0

        return self.position.distance(self.goal)

    # Define function to generate our children
    def children(self) -> List[Point]:
        # if there are no children then go ahead and generate the children
        # this is just an extra precaution that we don't want to children twice

        # print("Current state: ", self)
        if not self._children:
            # By default we only consider valid moves to get us to our desintation
            valid_moves = self.board.valid_snake_moves(self.snake)
            for move in valid_moves:
                self._create_child_for_move(move)

        # If we're aiming to get to a point in another snake, on the border,
        # or in ourselves (i.e. not really a "valid" snake move") we check
        # here to see if the goal is adjacent to the current point.
        if self.goal in Move.all_move_points(self.position):
            move = self.goal
            self._create_child_for_move(move)

        return self._children

    def _create_child_for_move(self, move):
        # create a child and store the value of the child and pass self to store the parent of the child
        new_snake = self.snake.move_toward(
            move, grow=(True if move in self.board.food else False)
        )
        # print("New Snake: ", new_snake)
        child = StateSnake(
            position=move,
            parent=self,
            start=self.start,
            goal=self.goal,
            board=self.board,
            snake=new_snake,
        )
        # finally add this child to our children list
        self._children.append(child)

    def __repr__(self):
        return f"SnakeState(current={self.position},_children={self._children}, snake={self.snake}"


class AStarSnakePathSolver:
    def __init__(
        self,
        snake: Snake,
        goal: Point,
        board: Board,
        move_snake: bool = True,
        alternate_limit: int = 0,
        move_limit: int = None,
        return_closest: bool = False,
    ):
        """
        Used to find a path from the snake's current position to a given other
        position on a game board.
        :param snake: The snake whose path we will find.
        :param goal: The objective point on the board to find.
        :param board: The board (with obstacles) to use in the path.
        :param move_snake: Whether the snake's movement (and freeing space) should be considered (i.e. True),
            or whether it's position should be static (i.e. False)
        :param alternate_limit: The maximum number of 2nd-best alternate path steps to test from the first 2nd-best
            alternative path found (i.e. the first time there is more than 1 choice).
        :param move_limit: The maximum number of moves before abandoning the search for a path.  This amounts to
            if the most direct path can't be done in less than the limit, the solver will quit.
        :param return_closest: Whether to return the closest path to the destination if the
            search limit is reached or no more moves are possible.
        """
        self.path = []  # store final solution from start state to goal state
        self.visited = []  # it keeps track all the children that are visited
        self.priorityQueue = PriorityQueue()
        self.start = snake.head  # store start state
        self.goal = goal  # store goal state
        self.board = board
        self.move_snake = move_snake
        self.alternate_limit = alternate_limit if alternate_limit >= 0 else 0
        self.return_closest = return_closest

        if not move_limit or move_limit < 1:
            move_limit = (board.size.x * board.size.y) - sum(
                [snake.size for snake in board.snakes]
            )

        # We add 1 because the AStar algorithm counts the head start position
        # in its count of moves.
        self.move_limit = move_limit + 1

        if move_snake:
            self.snake = snake

        else:
            # We create a copy of the snake, and giv it an ID
            # that no other snake will have, therefore board movement
            # will still track the position of the current snake.
            self.snake = copy.deepcopy(snake)
            snake.id = None

    def solve(self):
        start = time.perf_counter()
        try:
            # it doesn't have any parent state to start.
            start_state = StateSnake(
                position=self.start,
                parent=None,
                start=self.start,
                goal=self.goal,
                board=self.board,
                snake=self.snake,
            )

            move_count = 0

            # priorityQueue.put() is used to add children, you have to pass a tuple inside it.
            # The tuple contain 0, count and startState.
            # 0 is priority number that we want
            self.priorityQueue.put((0, move_count, start_state))

            add_alternate_route = self.alternate_limit > 0

            last_path = []

            # this while loop is where the magic happens
            while (
                not self.path
                and self.priorityQueue.qsize()
                and move_count < self.move_limit
            ):
                # print("Queue: ", self.priorityQueue.queue)

                # getting topmost value from the priority queue
                priority, move_count, closest_child = self.priorityQueue.get()
                # print(
                #     f"Closest Child (dist={priority} / moves={move_count}) State: ",
                #     closest_child.position,
                #     f"Path: {closest_child.path}",
                #     "Children: ",
                #     [child.position for child in closest_child.children()],
                # )

                # it keep track all the children that we are visited
                self.visited.append(closest_child.position)

                last_path = closest_child.path

                closest_child_children = closest_child.children()
                for child in closest_child_children:
                    # We're there!
                    if child.position == self.goal:
                        self.path = child.path
                        break

                    if child.position not in self.visited:
                        move_count = len(child.path)

                        # If we haven't arrived yet distance is not zero...
                        if child.dist:
                            self.priorityQueue.put((child.dist, move_count, child))

                # TODO: Experiment to see if we can pick the first alternate path found.
                # We'll only populate the alternate path for the staring position.
                if add_alternate_route and len(closest_child_children) > 1:
                    # We only check one alternate route, so disable adding another right away.
                    add_alternate_route = False

                    # Take the 2nd shortest route
                    alternate_state = sorted(
                        closest_child_children, key=lambda state: state.dist
                    )[1]

                    for alternate_cnt in range(0, self.alternate_limit):
                        # Take the shortest route at this point, until the limit...
                        alternate_state_children = alternate_state.children()
                        if not alternate_state_children:
                            break

                        alternate_state = sorted(
                            alternate_state_children, key=lambda state: state.dist
                        )[0]

                        self.priorityQueue.put(
                            (
                                alternate_state.dist,
                                len(alternate_state.path),
                                alternate_state,
                            )
                        )

                        if alternate_state.dist == 0:
                            break

            if not self.path:
                print(
                    f"Goal of {self.goal} is not possible after {move_count} moves! (max {self.move_limit})"
                )
                if self.return_closest:
                    return last_path

            return self.path
        finally:
            end = time.perf_counter()
            print(
                f"Took {end - start:0.3f} seconds to find path from {self.start} to {self.goal} in "
                + f"{len(self.path)} steps: {self.path}"
            )


def find_path(
    snake: Snake,
    goal: Point,
    board: Board,
    max_moves: int = None,
    alternate_limit: int = 0,
    move_snake: bool = False,
    return_closest: bool = False,
):
    path_solver = AStarSnakePathSolver(
        snake=snake,
        goal=goal,
        board=board,
        move_snake=move_snake,
        alternate_limit=alternate_limit,
        move_limit=max_moves,
        return_closest=return_closest,
    )
    return path_solver.solve()
