import chess
import chess.pgn
from analysis import analyse_game, engine
import evaluation
from game_evaluation import game_accuracy

def review_game(PGN_PATH):
    moves = []
    previous_eval = 0
    white_accuracy = []
    black_accuracy = []
    white_classifications = {}
    black_classifications = {}

    PGN_PATH = PGN_PATH.strip('"\'# ')

    with open(PGN_PATH) as pgn_file:
        game = chess.pgn.read_game(pgn_file)

        if game is None:
            return "Fail to load PGN"

        board = chess.Board()

        move_list = list(game.mainline_moves())
        total = len(move_list)

        for i, move in enumerate(move_list):
            engine_analysis_data = analyse_game(board, move)

            engine_move = engine_analysis_data["Best Move"]
            player_move = engine_analysis_data["Player Move"]
            turn = engine_analysis_data["Turn"]
            legal_moves = engine_analysis_data["Legal Moves"]
            
            before_score = evaluation.score(engine_analysis_data["Engine Info"]["score"])
            after_score = evaluation.score(engine_analysis_data["Player Info"]["score"])
            before_expectation_score, before_win, before_draw, before_loss = evaluation.wdl(engine_analysis_data["Engine Info"]["wdl"])

            if board.is_game_over():
                after_win, after_draw, after_loss = evaluation.wdl_gameover(board, turn)
                continue
            else:
                after_expectation_score, after_win, after_draw, after_loss = evaluation.wdl(engine_analysis_data["Player Info"]["wdl"])

            classification = evaluation.classification(engine_analysis_data["Engine Info"]["score"], engine_analysis_data["Player Info"]["score"], engine_move, player_move, turn, legal_moves)
            
            if turn == chess.WHITE:
                white_classifications[classification] = white_classifications.get(classification, 0) + 1
            else:
                black_classifications[classification] = black_classifications.get(classification, 0) + 1

            accuracy = evaluation.move_accuracy(before_expectation_score, after_expectation_score, turn)

            white_accuracy.append(accuracy) if turn == chess.WHITE else black_accuracy.append(accuracy)

            move_eval = f"Mate in {after_score}" if engine_analysis_data["Player Info"]["score"].is_mate() else f"{after_score/100:+.2f}"

            move_data = {
                "Move": i+1,
                "Player Move": player_move,
                "Best Move": engine_move,
                "Eval Before": previous_eval,
                "Eval After": move_eval,
                "Accuracy": accuracy,
                "Classification": classification,
                "WDL Win Prob": after_win,
                "WDL Draw Prob": after_draw,
                "WDL Loss Prob": after_loss,
                "Board FEN": board.fen()
            }

            moves.append(move_data)
            progress = int((i+1)/total*100)

        white_game_accuracy, black_game_accuracy = game_accuracy(white_accuracy, black_accuracy)

        return {
            "moves": moves,
            "white_accuracy": white_game_accuracy,
            "black_accuracy": black_game_accuracy,
            "white_classifications": white_classifications,
            "black_classifications": black_classifications,
            "headers": game.headers,
            "Progress": progress
        }
    engine.quit()
