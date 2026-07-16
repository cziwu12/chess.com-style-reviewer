"""Local web server for the chess reviewer.

Run: python web_app.py
Then open: http://127.0.0.1:8000
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from io import StringIO
import json
import chess
import chess.pgn

import evaluation
from analysis import analyse_game, engine
from game_evaluation import game_accuracy

ROOT = Path(__file__).resolve().parent


def score_text(score):
    white_score = evaluation.score(score)
    return f"Mate in {white_score}" if score.white().is_mate() else f"{white_score / 100:+.2f}"


def analyse_pgn(pgn_text):
    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        raise ValueError("No valid PGN game was found.")

    board = game.board()
    results, white_accuracy, black_accuracy = [], [], []
    classifications = {"white": {}, "black": {}}

    for index, move in enumerate(game.mainline_moves(), start=1):
        data = analyse_game(board, move)  # advances board to the player's position
        turn = data["Turn"]
        before_expectation, *_ = evaluation.wdl(data["Engine Info"]["wdl"])

        if board.is_game_over():
            _, win, draw, loss = evaluation.wdl_gameover(board, turn)
        else:
            after_expectation, win, draw, loss = evaluation.wdl(data["Player Info"]["wdl"])
            accuracy = evaluation.move_accuracy(before_expectation, after_expectation, turn)
            (white_accuracy if turn == chess.WHITE else black_accuracy).append(accuracy)

        # The evaluator expects player move first, then the engine move.
        classification = evaluation.classification(
            data["Engine Info"]["score"], data["Player Info"]["score"],
            data["Player Move"], data["Best Move"], turn, data["Legal Moves"]
        )
        side = "white" if turn == chess.WHITE else "black"
        classifications[side][classification] = classifications[side].get(classification, 0) + 1
        results.append({
            "number": index, "side": side, "player_move": data["Player Move"],
            "best_move": data["Best Move"], "evaluation": score_text(data["Player Info"]["score"]),
            "classification": classification, "accuracy": round(accuracy, 2) if not board.is_game_over() else 100.0,
            "win": win, "draw": draw, "loss": loss, "fen": data["Player Board FEN"]
        })

    white_score, black_score = game_accuracy(white_accuracy, black_accuracy) if white_accuracy and black_accuracy else (0, 0)
    return {"headers": dict(game.headers), "moves": results, "white_accuracy": round(white_score, 1),
            "black_accuracy": round(black_score, 1), "classifications": classifications,
            "starting_fen": game.board().fen()}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if self.path != "/api/analyse":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2_000_000:
                raise ValueError("PGN must be between 1 byte and 2 MB.")
            payload = json.loads(self.rfile.read(length))
            result = analyse_pgn(payload.get("pgn", ""))
            body, status = json.dumps(result).encode(), 200
        except Exception as error:
            body, status = json.dumps({"error": str(error)}).encode(), 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("Chess reviewer running at http://127.0.0.1:8000")
    try:
        ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
    finally:
        engine.quit()
