#!/usr/bin/env python3
# The above uses the environments `python` version (venv, or otherwise).
import argparse
import json
import os
import re
import sys
import uuid

from models import Board, Point


def eprint(message: str):
    print(message, file=sys.stderr, flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Creates a ASCII-art representation of the board into a file with the same name but the '.json' "
        "extension is changed (or aded) to be '.txt'. "
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-j", "--json", help="Path to the BattleSnake JSON game data file."
    )
    group.add_argument(
        "-s",
        "--size",
        help="Print an empty ASCII-art board for a board of a given size in the format "
        "'WxH' where 'W' is width and 'H' is height.",
    )
    group.add_argument(
        "-a",
        "--ascii",
        help="Path to the ASCII-art board to transform into a BattleSnake JSON game "
        "data file. Snakes are denoted by a single letter (upper-case for the head, "
        "lower case for body) and '+' for food.  The player snake is indicated by 'Y'"
        " and 'y'.  Note:  Besides the head, the snake's body will not be in order.",
    )

    args = parser.parse_args()

    if args.ascii:
        input_file = args.ascii

        if not os.path.isfile(input_file):
            eprint(
                f"Specified game board ASCII-art file does not exist: '{input_file}'"
            )
            sys.exit(1)

        snakes = []
        food = []
        board = {"food": food, "snakes": snakes}
        you = {"id": str(uuid.uuid4()), "name": "you", "health": 100}
        game = {
            "game": {"id": str(uuid.uuid4()), "timeout": 500},
            "turn": 1,
            "board": board,
            "you": you,
        }

        snake_lookup = {}

        cell_re = re.compile(r".*\s(\s|[a-zA-Z]|\+)\s.*")
        with open(input_file, "r") as table:
            width = None
            height = 0
            rows = []
            for line in table.readlines():

                if "│" not in line:
                    continue

                height += 1
                columns = line.split("│")
                if not width:
                    # Use the size of the first row to determine the board width
                    width = len(columns)

                columns = list(cell_re.search(cell).group(1) for cell in columns)

                rows.append(columns)

            board["height"] = height
            board["width"] = width

            for r_pos, row in enumerate(rows):
                for c_pos, column in enumerate(row):
                    # X-axis counts up from left to right
                    x = c_pos
                    # Y-axis counts down to zero from top to bottom
                    y = height - r_pos - 1

                    if not column.strip():
                        continue

                    elif column == "+":
                        food.append({"x": x, "y": y})
                        continue

                    if column.upper() not in snake_lookup:
                        new_snake = {
                            "id": str(uuid.uuid4()),
                            "name": column.upper(),
                            "health": 100,
                            "body": [{"x": x, "y": y}],
                            "shout": "",
                        }

                        if column.isupper():
                            new_snake["head"] = {"x": x, "y": y}

                        snake_lookup[column.upper()] = new_snake

                    else:
                        next_snake = snake_lookup[column.upper()]

                        if column.isupper():
                            next_snake["head"] = {"x": x, "y": y}
                            next_snake["body"].insert(0, {"x": x, "y": y})
                        else:
                            next_snake["body"].append({"x": x, "y": y})

            for snake_name, snake_details in snake_lookup.items():
                snake_details["length"] = len(snake_details["body"])

                if snake_name == "Y":
                    game["you"] = snake_details

                game["board"]["snakes"].append(snake_details)

            if input_file.endswith(".txt"):
                output_file = input_file[: input_file.rfind(".txt")] + ".json"
            else:
                output_file = input_file + ".json"

            print(f"Output: {output_file}")

            with open(output_file, "w") as output:
                output.write(json.dumps(game, indent=2))

    elif args.size:
        x, y = args.size.split("x")
        board = Board(
            game_id=None,
            my_id=None,
            snakes={},
            food=[],
            heat=None,
            size=Point(int(x), int(y)),
        )

        print(board)

    elif args.json:
        input_file = args.json
        if not os.path.isfile(input_file):
            eprint(
                f"Specified BattleSnake game JSON file does not exist: '{input_file}'"
            )
            sys.exit(1)

        if input_file.endswith(".json"):
            output_file = input_file[: input_file.rfind(".json")] + ".txt"
        else:
            output_file = input_file + ".txt"

        print(f"Output: {output_file}")

        board = _load_game_board(input_file)

        with open(output_file, "w") as output:
            output.write(str(board))


def _load_game_board(data_path: str) -> dict:
    with open(os.path.realpath(data_path)) as f:
        return Board.parse(json.load(f))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
