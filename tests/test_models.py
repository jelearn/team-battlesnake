from typing import List

from models import HeatMap, HeatType, Heat, Point, Snake, Board
from game import is_closest_strongest_snake


def test_point_in_set():
    p1 = Point(0, 0)
    p2 = Point(0, 1)
    p3 = Point(0, 2)
    p4 = Point(1, 0)

    set1 = set()

    set1.add(p1)
    set1.add(p2)

    assert p1 in set1
    assert p2 in set1

    assert p3 not in set1
    assert p4 not in set1


def test_point_in_dict():
    p1 = Point(0, 0)
    p2 = Point(0, 1)
    p3 = Point(0, 2)
    p4 = Point(1, 0)

    dict1 = {p1: 1, p2: 2}

    assert p1 in dict1
    assert p2 in dict1

    assert p3 not in dict1
    assert p4 not in dict1


def test_heatmap_goodness():
    hm = HeatMap()

    food = Heat("food", HeatType.GOOD, value=2)
    empty = Heat("empty", HeatType.NONE)
    future_snake = Heat("future_snake", HeatType.DANGER)
    snake_body = Heat("snake_body", HeatType.DEATH)
    death = Heat("death", HeatType.DEATH)

    p1 = Point(0, 0)
    p2 = Point(0, 1)
    p3 = Point(0, 2)
    p4 = Point(1, 0)

    assert (
        hm.goodness(p1) == 0
    ), "By default, if the points not there, it's empty and safe"

    hm.add(p1, food)

    assert hm.goodness(p1) == 2001, "Safe things should increment."

    hm.add(p1, future_snake)

    assert hm.goodness(p1) == 991, "Danger should decrements."

    hm.add(p2, snake_body)

    assert hm.goodness(p2) == HeatMap.DEATH_HEAT, "Death is ultimate non-goodness."

    hm.add(p3, empty)
    hm.add(p3, future_snake)

    assert hm.goodness(p3) == -10

    hm.add(p4, death)

    assert hm.goodness(p4) == HeatMap.DEATH_HEAT, "Death is negative maximum heat."

    hm.add(p4, food)
    hm.add(p4, empty)

    assert hm.goodness(p4) == HeatMap.DEATH_HEAT, (
        "Once marked with Death, the goodness score should be negative " "max heat. "
    )
    hm.add(p4, snake_body)

    assert (
        hm.goodness(p4) == HeatMap.DEATH_HEAT
    ), "Adding more danger, should not negate the death heat."


def test_heatmap_has_heat():
    hm = HeatMap()

    food = Heat("food", HeatType.GOOD, value=2)
    empty = Heat("empty", HeatType.NONE)
    future_snake = Heat("future_snake", HeatType.POSSIBLE_DEATH)
    snake_body = Heat("snake_body", HeatType.DEATH)
    death = Heat("death", HeatType.DEATH)

    p1 = Point(0, 0)

    assert not hm.has_heat(p1, food)
    assert not hm.has_heat(p1, empty)
    assert not hm.has_heat(p1, future_snake)
    assert not hm.has_heat(p1, snake_body)
    assert not hm.has_heat(p1, death)

    hm.add(p1, food)

    assert hm.has_heat(p1, food)
    assert not hm.has_heat(p1, empty)
    assert not hm.has_heat(p1, future_snake)
    assert not hm.has_heat(p1, snake_body)
    assert not hm.has_heat(p1, death)

    hm.add(p1, future_snake)

    assert hm.has_heat(p1, food)
    assert not hm.has_heat(p1, empty)
    assert hm.has_heat(p1, future_snake)
    assert not hm.has_heat(p1, snake_body)
    assert not hm.has_heat(p1, death)

    hm.add(p1, snake_body)

    assert hm.has_heat(p1, food)
    assert not hm.has_heat(p1, empty)
    assert hm.has_heat(p1, future_snake)
    assert hm.has_heat(p1, snake_body)
    assert not hm.has_heat(p1, death)

    hm.add(p1, empty)

    assert hm.has_heat(p1, food)
    assert hm.has_heat(p1, empty)
    assert hm.has_heat(p1, future_snake)
    assert hm.has_heat(p1, snake_body)
    assert not hm.has_heat(p1, death)

    hm.add(p1, death)

    assert hm.has_heat(p1, food)
    assert hm.has_heat(p1, empty)
    assert hm.has_heat(p1, future_snake)
    assert hm.has_heat(p1, snake_body)
    assert hm.has_heat(p1, death)


def test_heatmap_heat_escalation():
    hm = HeatMap()

    empty = Heat("conflict", HeatType.NONE)
    food = Heat("conflict", HeatType.GOOD, value=2)
    future_snake = Heat("conflict", HeatType.DANGER, value=3)
    snake_body = Heat("conflict", HeatType.DEATH)

    p1 = Point(0, 0)

    assert (
        hm.goodness(p1) == 0
    ), "By default, if the points not there, it's empty and safe."

    hm.add(p1, empty)

    assert hm.goodness(p1) == 1000, "Empty maintains goodness"

    hm.add(p1, food)

    assert hm.goodness(p1) == 3001, "Good increases"

    hm.add(p1, future_snake)

    assert hm.goodness(p1) == -9, "Danger reduces priority."

    hm.add(p1, snake_body)

    assert hm.goodness(p1) == HeatMap.DEATH_HEAT, "Death takes priority"

    hm.add(p1, food)

    assert hm.goodness(p1) == HeatMap.DEATH_HEAT, "De-escalation is not possible"


def test_is_closest_strongest_snake():
    me = Snake(id="1", name="me", health=1, body=[Point(10, 1), Point(9, 1)])
    other = Snake(id="2", name="other", health=1, body=[Point(8, 3), Point(7, 3)])

    assert is_closest_strongest_snake(
        target=Point(10, 0),
        check_snake=me,
        board=_make_test_board(me, [other]),
        max_competition=1,
        min_buffer=5,
    )


def test_is_closest_strongest_snake2():
    me = Snake(id="1", name="me", health=1, body=[Point(10, 1), Point(9, 1)])
    other = Snake(id="2", name="other", health=1, body=[Point(8, 3), Point(7, 3)])
    other2 = Snake(id="3", name="other2", health=1, body=[Point(9, 7), Point(9, 8)])
    assert is_closest_strongest_snake(
        target=Point(10, 0),
        check_snake=me,
        board=_make_test_board(me, [other]),
        max_competition=1,
        min_buffer=20,
    )


def test_is_closest_strongest_snake3():
    me = Snake(id="1", name="me", health=1, body=[Point(10, 1), Point(9, 1)])
    other = Snake(id="2", name="other", health=1, body=[Point(8, 3), Point(7, 3)])

    assert not is_closest_strongest_snake(
        target=Point(8, 2),
        check_snake=me,
        board=_make_test_board(me, [other]),
        max_competition=1,
        min_buffer=3,
    )


def test_is_closest_strongest_snake4():
    me = Snake(id="1", name="me", health=1, body=[Point(10, 1), Point(9, 1)])
    other = Snake(id="2", name="other", health=1, body=[Point(8, 3), Point(7, 3)])
    other2 = Snake(id="3", name="other2", health=1, body=[Point(9, 7), Point(9, 8)])

    assert is_closest_strongest_snake(
        target=Point(10, 0),
        check_snake=me,
        board=_make_test_board(me, [other, other2]),
        max_competition=1,
        min_buffer=20,
    )


def test_is_closest_strongest_snake5():
    me = Snake(id="1", name="me", health=1, body=[Point(10, 1), Point(9, 1)])
    other = Snake(id="2", name="other", health=1, body=[Point(8, 3), Point(7, 3)])
    other2 = Snake(id="3", name="other2", health=1, body=[Point(9, 7), Point(9, 8)])

    assert not is_closest_strongest_snake(
        target=Point(8, 2),
        check_snake=me,
        board=_make_test_board(me, [other, other2]),
        max_competition=1,
        min_buffer=20,
    )


def _make_test_board(me: Snake, others: List[Snake]):
    board = Board(
        game_id="test",
        my_id=me.id,
        size=Point(11, 11),
        snakes=dict((snake.id, snake) for snake in [me] + others),
        food=[],
        heat=HeatMap(),
    )

    return board
