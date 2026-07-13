import chess
import chess.pgn
from analysis import analyse_game, engine
import evaluation
from game_evaluation import game_accuracy
import traceback

moves = []
previous_eval = 0
white_accuracy = []
black_accuracy = []
white_classifications = {}
black_classifications = {}

try:
    PGN_PATH = input("PGN File Path: ").strip('"\'# ')

    with open(PGN_PATH) as pgn_file:
        game = chess.pgn.read_game(pgn_file)

        if game is None:
            print("Fail to load PGN")
        else:
            print(game.headers["Event"])

        board = chess.Board()

        for i, move in enumerate(game.mainline_moves()):
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

            '''
            if turn == chess.WHITE:
                if classification in white_classifications:
                    white_classifications[classification] += 1
                else:
                    white_classifications[classification] = 1
            else:
                if classification in black_classifications:
                    black_classifications[classification] += 1
                else:
                    black_classifications[classification] = 1
            '''
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

        for move in moves:
            print("-----------------")
            print(f"\nMove {move["Move"]}")
            print(f"\nPlayer Move: {move["Player Move"]}")
            print(f"\nBest Move: {move["Best Move"]}")
            print(f"\nEval: {move["Eval Before"]} -> {move["Eval After"]}")
            print(f"\nClassification: {move["Classification"]}")
            print(f"\nWDL Prob: Win: {move["WDL Win Prob"]}% | Draw: {move["WDL Draw Prob"]}% | Loss: {move["WDL Loss Prob"]}%")
            print(f"\nBoard Fen: {move["Board FEN"]}")
            print("\n-----------------")

        white_game_accuracy, black_game_accuracy = game_accuracy(white_accuracy, black_accuracy)
        print(f"White Game Accuracy: {white_game_accuracy:.2f}%")
        print(f"Black Game Accuracy: {black_game_accuracy:.2f}%") 

        print("\nWhite Classifications")
        for white_classification in white_classifications:
            print(f"- {white_classification}: {white_classifications[white_classification]}")

        print("\nBlack Classifications")
        for black_classification in black_classifications:
            print(f"- {black_classification}: {black_classifications[black_classification]}")

except Exception as e:
    print(e)
    print(traceback.format_exc())
finally:
    engine.quit()