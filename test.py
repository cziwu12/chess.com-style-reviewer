import chess
import chess.engine
import chess.pgn
import traceback
import math

engine = chess.engine.SimpleEngine.popen_uci(r"C:\Users\notcz\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe")

engine.configure({"UCI_ShowWDL": True})

PIECE_VALUES = {
    chess.PAWN: 100,      
    chess.KNIGHT: 300,    
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 100000
}

white_accuracy = []
black_accuracy = []

#1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6 5. Nxe5 Bxd1 6. Bxf7+ Ke7 7. Nd5# 1-0
def game_accuracy(white_accuracy, black_accuracy):
    white_weights = []
    black_weights = []
    total_moves = len(white_accuracy) + len(black_accuracy)

    for i in white_accuracy:
        i_weight = 1 + ((8 * math.sqrt(total_moves / 45)) / (1 + math.exp(-12 * (abs(i / 100) - 0.2))))
        white_weights.append(i_weight)
    
    for u in black_accuracy:
        u_weight = 1 + ((8 * math.sqrt(total_moves / 45)) / (1 + math.exp(-12 * (abs(u / 100) - 0.2))))
        black_weights.append(u_weight)

    white_game_accuracy = sum(ww * wl for ww, wl in zip(white_weights, white_accuracy)) / sum(white_weights)
    black_game_accuracy = sum(bw * bl for bw, bl in zip(black_weights, black_accuracy)) / sum(black_weights)

    return white_game_accuracy, black_game_accuracy


def move_accuracy(before_score, after_score, turn):
    if before_score is None or after_score is None:
        return 99.9 if turn == chess.WHITE else 0.01
    
    loss = max(0, before_score - after_score) * 100 if turn == chess.WHITE else max(0, after_score - before_score) * 100

    accuracy = 103.1668 * math.exp(-0.04354 * loss) - 3.1669
    accuracy = max(0, min(100, accuracy))
    white_accuracy.append(accuracy) if turn == chess.WHITE else black_accuracy.append(accuracy)

    return round(max(0, accuracy), 2)

try:
    PGN_PATH = input("PGN File Path: ").strip('"\'# ')

    with open(PGN_PATH) as pgn_file:
        game = chess.pgn.read_game(pgn_file)

        if game is None:
            print("Fail to load PGN")
        else:
            print(game.headers["Event"])

            board = chess.Board()
            ply = 0

            for i, move in enumerate(game.mainline_moves()):
                turn = board.turn

                #analysing initial board and get the engine move
                board_sim = board.copy()
                before_info = engine.analyse(board_sim, chess.engine.Limit(time=1, depth=22)) #before engine move is played (empty board)

                #get all the moves by the engine
                all_engine_moves = before_info["pv"][0] #[pv["pv"][0] for pv in before_info] 

                #get the best engine move an convert it to SAN format
                #engine_move = all_engine_moves[0]
                engine_san = board_sim.san(all_engine_moves)

                #show the engine move on the board along with other info
                board_sim.push(all_engine_moves)
                print(f"No{i+1}. Engine Move: {engine_san} ({all_engine_moves}) \n {board_sim}")

                beforewdl = before_info["wdl"]

                before_score = beforewdl.white().expectation()

                print(beforewdl)
                print(before_score)  
                print(f"WDL Prob: Win: {beforewdl.white().wins / 10}% | Draw: {beforewdl.white().draws / 10}% | Loss: {beforewdl.white().losses / 10}%")

                print("|———————————————|")

                #convert player move to SAN format and play the mvpe
                player_san = board.san(move)
                board.push(move)
                print(f"Player Move: {player_san} ({move}) \n {board}")
                after_info = engine.analyse(board, chess.engine.Limit(time=1, depth=22))  #after player move is played (e4 board)
                legal_moves = list(board.legal_moves)

                if board.is_game_over():
                    if board.is_stalemate():
                        after_score = 0.5
                    elif turn == chess.WHITE:
                        after_score = 1.0
                    else:
                        after_score = 0.0

                    print(after_score)
                else:
                    afterwdl = after_info["wdl"]

                    after_score = afterwdl.white().expectation()

                    print(afterwdl)
                    print(after_score)  
                    print(f"WDL Prob: Win: {afterwdl.white().wins / 10}% | Draw: {afterwdl.white().draws / 10}% | Loss: {afterwdl.white().losses / 10}%")             

                print("|———————————————|")
                player_move_accuracy = move_accuracy(before_score, after_score, turn)
                print(player_move_accuracy)
            

                print("~-~-~-~-~-~-~-~-~")

            print("Game Over")
            white_game_accuracy, black_game_accuracy = game_accuracy(white_accuracy, black_accuracy)   
            print(f"White Game Accuracy: {round(white_game_accuracy, 2)}%")
            print(f"Black Game Accuracy: {round(black_game_accuracy, 2)}%")
except Exception as e:
    print(e)
    print(traceback.format_exc())
finally:
    engine.quit()


