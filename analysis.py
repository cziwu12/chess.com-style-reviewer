from pathlib import Path
import chess.engine
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

stockfish_dir = BASE_DIR / "stockfish"

try:
    STOCKFISH_PATH = next(stockfish_dir.glob("stockfish*.exe"))
except StopIteration:
    raise FileNotFoundError(f"No Stockfish executable found in {stockfish_dir}")

engine = None

def get_engine():
    global engine

    if engine is None:
        engine = chess.engine.SimpleEngine.popen_uci(str(STOCKFISH_PATH))
        engine.configure({"UCI_ShowWDL": True})

    return engine

def analyse_game(board, move):
        turn = board.turn

        legal_moves = list(board.legal_moves)

        board_sim = board.copy()
        engine = get_engine()

        before_info = engine.analyse(board_sim, chess.engine.Limit(time=1, depth=22)) 

        engine_move = before_info["pv"][0]
        engine_san = board_sim.san(engine_move)

        board_sim.push(engine_move)
        before_board_fen = board_sim.fen()

        player_san = board.san(move)
        board.push(move)
        player_board_fen = board.fen()

        after_info = engine.analyse(board, chess.engine.Limit(time=1, depth=22)) 
        return {
            "Best Move": engine_san,
            "Player Move": player_san,
            "Engine Board FEN": before_board_fen,
            "Player Board FEN": player_board_fen,
            "Engine Info": before_info,
            "Player Info": after_info,
            "Turn": turn,
            "Legal Moves": legal_moves
        }

def quit_engine():
    global engine

    if engine is not None:
        engine.quit()
        engine = None