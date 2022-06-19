import pytest

from models import Board, Point
from astar import AStarSnakePathSolver
from tests.test_server import _load_game_data


@pytest.fixture()
def test_board():
    game_data = _load_game_data("future_dead_end_007.json")
    board = Board.parse(game_data)
    return board


def test_find_tail(test_board: Board):
    goal = test_board.me.tail

    print(f"From {test_board.me.head} to {goal}")
    a = AStarSnakePathSolver(test_board.me, goal, test_board)  # Initializing object
    a.solve()  # call Solve() method

    for i in range(len(a.path)):  # printing the result
        print("{0}){1}".format(i, a.path[i]))

    assert a.path, "A path should have been found."

    assert a.path == [
        Point(1, 0),
        Point(2, 0),
        Point(2, 1),
        Point(3, 1),
        Point(3, 2),
        Point(4, 2),
    ]


def test_find_other_snake_head(test_board: Board):
    goal = Point(3, 4)

    print(f"From {test_board.me.head} to {goal}")
    a = AStarSnakePathSolver(test_board.me, goal, test_board)  # Initializing object
    a.solve()  # call Solve() method

    for i in range(len(a.path)):  # printing the result
        print("{0}){1}".format(i, a.path[i]))

    assert a.path, "A path should have been found."

    print(a.path)

    assert a.path == [
        Point(1, 0),
        Point(2, 0),
        Point(2, 1),
        Point(2, 2),
        Point(2, 3),
        Point(2, 4),
        Point(3, 4),
    ]


def test_find_other_snake_head_without_movement(test_board: Board):
    goal = Point(3, 4)

    print(f"From {test_board.me.head} to {goal}")
    a = AStarSnakePathSolver(
        test_board.me, goal, test_board, move_snake=False
    )  # Initializing object
    a.solve()  # call Solve() method

    for i in range(len(a.path)):  # printing the result
        print("{0}){1}".format(i, a.path[i]))

    assert a.path, "A path should have been found."

    print(a.path)

    # NOTE: This is the LONG way, without testing the 2nd best path
    # we'll end-up taking the long way around.
    assert a.path == [
        Point(1, 0),
        Point(2, 0),
        Point(2, 1),
        Point(3, 1),
        Point(4, 1),
        Point(5, 1),
        Point(5, 2),
        Point(6, 2),
        Point(6, 3),
        Point(6, 4),
        Point(6, 5),
        Point(6, 6),
        Point(5, 6),
        Point(5, 7),
        Point(4, 7),
        Point(3, 7),
        Point(3, 6),
        Point(3, 5),
        Point(3, 4),
    ]


def test_find_other_snake_head_without_movement_and_alternate(test_board: Board):
    goal = Point(3, 4)

    print(f"From {test_board.me.head} to {goal}")
    a = AStarSnakePathSolver(
        test_board.me, goal, test_board, move_snake=False, alternate_limit=3
    )  # Initializing object
    a.solve()  # call Solve() method

    for i in range(len(a.path)):  # printing the result
        print("{0}){1}".format(i, a.path[i]))

    assert a.path, "A path should have been found."

    print(a.path)

    assert a.path == [
        Point(1, 0),
        Point(0, 0),
        Point(0, 1),
        Point(0, 2),
        Point(0, 3),
        Point(1, 3),
        Point(2, 3),
        Point(2, 4),
        Point(3, 4),
    ]
