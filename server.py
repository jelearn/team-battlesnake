"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""

import argparse
import os
import time

import cherrypy

from game import Game


class Battlesnake(object):
    """
    The class to encapsulate the server that will expose the BattleSnake REST API
    to participate in games.
    """

    def __init__(
        self,
        author: str,
        color: str = "",
        head_type: str = "",
        tail_type: str = "",
    ):
        self.games = {}
        self._author = author
        self._color = color
        self._head_type = head_type
        self._tail_type = tail_type

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        # If you open your snake URL in a browser you should see this message.
        return {
            "apiversion": "1",
            "author": self._author,
            "color": self._color,
            "head": self._head_type,
            "tail": self._tail_type,
        }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def start(self):
        # This function is called every time your snake is entered into a game.
        # cherrypy.request.json contains information about the game that's about to be played.
        g, data = self.game_from_request()

        g.start(data)

        return "OK"

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def move(self):

        # This function is called on every turn of a game. It's how your snake decides where to move.
        # Valid moves are "up", "down", "left", or "right".
        g, data = self.game_from_request()

        print(f"TURN {g.turn} beginning...")
        start = time.perf_counter()
        try:
            return g.move(data)
        finally:
            end = time.perf_counter()
            print(f"TURN {g.turn} response in {end - start:0.3f} seconds")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def end(self):
        # This function is called when a game your snake was in ends.
        # It's purely for informational purposes, you don't have to make any decisions here.
        g, data = self.game_from_request()

        result = g.end(data)

        self.games.pop(g.game_id, None)

        return result

    def game_from_request(self):
        """
        :return: A Game object for the specified game, and the current request data.
        """
        # TODO: This has thread safety issues that should probably be addressed
        data = cherrypy.request.json
        _id = data["game"]["id"]
        if _id in self.games:
            game = self.games[_id]
            game.turn = int(data["turn"])
            return game, data
        else:
            g = Game(data)
            self.games[_id] = g
            return g, data


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Starts a BattleSnake server.")

    parser.add_argument(
        "-a",
        "--author",
        help="The BattleSnake user name to return as part of the v1 API.",
        required=True,
    )

    parser.add_argument(
        "-p",
        "--port",
        help="The port number for the server",
        default=8080,
        required=False,
    )

    parser.add_argument(
        "--color",
        help="The snake color, in HTML hexadecimal format.",
        default="#A8894F",
        required=False,
    )

    parser.add_argument(
        "--head",
        help="The head style of the snake.",
        default="fang",
        required=False,
    )

    parser.add_argument(
        "--tail",
        help="The tail style of the snake.",
        default="curled",
        required=False,
    )

    args = parser.parse_args()

    print(
        f"Snake: Author = {args.author} / Color = {args.color} / Head = {args.head} / Tail = {args.tail}"
    )

    server = Battlesnake(args.author, args.color, args.head, args.tail)
    cherrypy.config.update(
        {
            "server.socket_host": "0.0.0.0",
            # On heroku, the port is defined in PORT
            "server.socket_port": int(os.environ.get("PORT", args.port)),
        }
    )
    print("Starting Battlesnake Server...")
    cherrypy.quickstart(server)
