import json
import os
import time

import pytest

from game import Game

# We must respond within 500ms so we pick something lower to make
# sure we don't take too long to respond with any algorithm.
MAX_MOVE_TIME = 250 / 1000

# Where to store profiling output
PROFILES_DIR = "profiles"


def _load_game_data(data_path: str) -> dict:
    with open(
        os.path.realpath(
            os.path.join(os.path.dirname(__file__), "game_data", data_path)
        )
    ) as f:
        return json.load(f)


def assert_move_decision(expected_move, game_data_path: str):
    game_data = _load_game_data(game_data_path)
    test_game = Game(game_data)

    if isinstance(expected_move, list):
        assert test_game.move(game_data)["move"] in expected_move
    else:
        assert test_game.move(game_data)["move"] == expected_move


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        ("future_dead_end_001.json", "left"),
        ("future_dead_end_002.json", "down"),
        ("future_dead_end_003.json", "left"),
        ("future_dead_end_004.json", "right"),
        ("future_dead_end_005.json", "down"),
        ("future_dead_end_006.json", "right"),
        # In 3 moves (snacky) will create a dead-end with us because we chose the corner
        ("future_dead_end_007.json", "right"),
        ("future_dead_end_008.json", "right"),
        ("future_dead_end_009.json", "right"),
        # TODO: This dead-end is done by attacking a weaker snake that eventually
        #   closes the gap and blocks us in.
        # ("future_dead_end_010.json", "down"),
    ],
)
def test_future_dead_end_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        ("avoid_danger_001.json", "down"),
        ("avoid_danger_002.json", "right"),
        # TODO: Replace this, it was moved to killing move 004
        # ("avoid_danger_003.json", "right"),
        # 004: Right means goto corner for food
        #      Left means go towards stronger snake tail
        ("avoid_danger_004.json", "right"),
        # 004_part2: Up means towards a stringer snake, down at least means away (and eventually towards a weaker snake)
        ("avoid_danger_004_part2.json", "up"),
        ("avoid_danger_005.json", "left"),
        ("avoid_danger_006.json", "right"),
        ("avoid_danger_007.json", "right"),
        # Moving "left" off the edge is more important (because of future safety)
        # than immediate safety of going "down"
        ("avoid_danger_008.json", "left"),
        ("avoid_danger_009.json", "left"),
        # "left" means towards stronger snake, but "up"/"right' at least are away... but on edge.
        ("avoid_danger_010.json", ["up", "right"]),
        ("avoid_danger_011.json", "right"),
        ("avoid_danger_012.json", "down"),
        # Avoiding the edges gives us the most options (so "up" and "right" should be avoided unless last resort)
        #  However it depends on the snakes next move, if they go right, down is bad.
        #  If they go up, "up" is bad.  "right" is therefore a good middle ground.
        ("avoid_danger_013.json", "right"),
        # "left" is a 2-way food competition and no choices next round, should be avoided.
        # "right" is the edge and may block ourselves in, but it's not immediate death.
        # "down" may involve death in the following rounds, but it's not guaranteed.
        ("avoid_danger_014.json", ["down", "right"]),
        ("avoid_danger_015.json", "up"),
        # TODO: Going right creates more open space long-term
        #   and a more defensible position.
        #   Apply potential space calculation to solve this.
        # ("avoid_danger_016.json", "right"),
        ("avoid_danger_017.json", ["up", "right"]),
        ("avoid_danger_018.json", "down"),
    ],
)
def test_avoid_danger_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        ("killing_block_001.json", "left"),
        # Going "left" is bad because it's will eventually be
        #  a dead end with a stronger snake, need to trap the stronger
        #  snake by going up.
        ("killing_block_002.json", "up"),
        ("killing_block_003.json", "right"),
        # TODO: This is an opportunity to block someone in, they are far enough away
        #   that going left (then up) or just going up, would be good enough.
        #   really going up right away would probably be best, but we'll get there eventually.
        ("killing_block_004.json", ["left", "up"]),
        ("killing_block_005.json", "up"),
    ],
)
def test_killing_block_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        # TODO: Revisit safety or food... getting food might result
        #  in a dead-end and death.  Safety means keeping one step ahead
        #  of a stronger snake...
        # SAFETY
        ("safety_or_food_001.json", "up"),
        # FOOD (for now)
        # ("safety_or_food_001.json", "left"),
    ],
)
def test_safety_or_food_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move", [("food_when_starving_001.json", "left"),],
)
def test_food_when_starving_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        ("food_under_attack_001.json", "down"),
        # Originally this was "right" because it's safest because "down" is getting closer
        # to a stronger snake, however changing the "fear" (and avoiding edges) threshold this is ok.
        # Finally, it was changed to go down because the attacking snakes are still far enough away.
        ("food_under_attack_002.json", "down"),
        ("food_under_attack_003.json", "right"),
    ],
)
def test_food_under_attack_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.skip(
    reason="need to review this edge case, the corner is might not be the best"
)
def test_use_corner_when_needed_001():
    # The logic is go right to give yourself as much space as possible.
    assert_move_decision("right", "use_corner_when_needed_001.json")


@pytest.mark.skip(reason="these ar really tough cases")
@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        # Going "down" is immediately safest, however "left"/"down" risk death but may
        # create safety by blocking or maximizing open space (assuming they don't choose it)
        ("catch_22_001.json", "up"),
        # Going left  has most options and is farther than a stronger snake,
        # however going "up" would seem to give us more long term options.
        ("catch_22_002.json", "up"),
        # going "down" may get a kill, but leaves us with no choice when facing
        # a stronger snake, going, "left" still may give us a kill but
        # will also give us 1 more chance to live.
        ("catch_22_003.json", "left"),
    ],
)
def test_catch_22(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        # Going up is immediately safest, left/down risk death but may create
        # safety by blocking or maximizing open space (assuming they don't choose it)
        ("attack_weaker_snake_001.json", "up"),
        ("attack_weaker_snake_002.json", ["down", "left"]),
        ("attack_weaker_snake_003.json", "up"),
        # Choose one of the weak snake's next moves:
        ("attack_weaker_snake_004.json", ["up", "right"]),
        ("attack_weaker_snake_005.json", "left"),
        # TODO: We should be attacking the weaker snake, but they are really
        #   far away, going "up" might actually be risky, "down" gives lots of space.
        ("attack_weaker_snake_006.json", "up"),
        # ("attack_weaker_snake_006.json", "down"),
        # TODO: We should be attacking the weaker snake AND
        #   avoid large dead-end at bottom.
        ("attack_weaker_snake_007.json", "up"),
    ],
)
def test_attack_weaker_snake_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        # In this case we're far away enough from danger, we shouldn't use the edge
        ("avoid_edges_when_possible_001.json", ["up", "left"]),
    ],
)
def test_avoid_edges_when_possible_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


# @pytest.mark.skip(reason="For now we're being more aggressive.")
@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        # When we're attacking a weaker snake, and another starts attacking us, break-off if it's risky.
        ("attack_weaker_snake_abort_001.json", "down"),
    ],
)
def test_attack_weaker_snake_abort_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        # Only one snake left, equal strength, go to food?
        ("under_attack_001.json", ["up", "right"]),
        # Going "up" is technically closer to a stronger snake, but
        # it provides an opportunity to block the snake using the
        # other snakes body.  However "right" is probably the safest move>
        # TODO: implement/test for blocking opportunities
        # ("under_attack_002.json", "up"),
        ("under_attack_002.json", "right"),
        # Going up is normally more dangerous (because it's on the edge)
        # however going left will allow us to chase our tail for defense.
        # CHANGE: This position is no win, either way has equal chance of death.
        # ("under_attack_003.json", "left"),
        # Apply chase tail defense here by going "down".
        ("under_attack_004.json", "down"),
        # We're weak and under attack, we should use chase tail defense
        ("under_attack_005.json", "left"),
        # TODO: Going "up" creates a loop with itself to avoid being exposed
        #   to stronger snakes however it's tough to quantify when to be afraid
        #   of an attacking snake and when not to be.
        # ("under_attack_006.json", "up"),
        # Going "right" will end-up being a dead-end, "left" is the safer route when under attack.
        ("under_attack_007.json", "left"),
    ],
)
def test_under_attack_decisions(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


def _get_all_boards_expect_any_moves():
    test_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "game_data"))

    return [
        test_file for test_file in os.listdir(test_dir) if test_file.endswith(".json")
    ]


import cProfile


@pytest.mark.parametrize("game_data_path", _get_all_boards_expect_any_moves())
def test_decide_fast(tmpdir, game_data_path):
    start = time.perf_counter()

    profile_path = os.path.join(str(tmpdir), game_data_path + ".profile")

    try:
        game_data = _load_game_data(game_data_path)
        test_game = Game(game_data)

        cProfile.runctx(
            "test_game.move(game_data)", globals(), locals(), profile_path,
        )

    finally:
        end = time.perf_counter()

    runtime = end - start
    assert (
        runtime < MAX_MOVE_TIME
    ), f"Must finish under 500 ms. (i.e. {MAX_MOVE_TIME} ms), but took {runtime} see {profile_path} for profiling information."


@pytest.mark.parametrize(
    "game_data_path,expected_move", [("just_get_food_001.json", "left"),],
)
def test_just_get_food(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        ("favor_forward_001.json", "left"),
        # With improvements to danger protection "up" is safer (but is not forward)
        ("favor_forward_002.json", "up"),
        ("favor_forward_003.json", "left"),
        # This is also an avoid danger moves (not just favor forward)
        # so if it happens to go "up" to safety, that's ok.
        ("favor_forward_004.json", ["left", "up"]),
        # Going-up leaves space within body for backup moves.
        ("favor_forward_005.json", "up"),
    ],
)
def test_favor_forward(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move", [("use_edge_when_needed_001.json", "down"),],
)
def test_use_edge_when_needed(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)


@pytest.mark.parametrize(
    "game_data_path,expected_move",
    [
        ("solo_survival_001.json", "left"),
        ("solo_survival_002.json", "right"),
        ("solo_survival_003.json", "right"),
        # Going "up" get's food, but it puts us in a better position for
        # following our tail... however "left" technically is free.
        ("solo_survival_004.json", "left"),
        ("solo_survival_005.json", "down"),
    ],
)
def test_solo_survival(game_data_path, expected_move):
    assert_move_decision(expected_move, game_data_path)
