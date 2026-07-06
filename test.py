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

#1. e4 e5 2. Nf3 d6 3. Bc4 Bg4 4. Nc3 g6 5. Nxe5 Bxd1 6. Bxf7+ Ke7 7. Nd5# 1-0

def move_accuracy(before_score, after_score, turn):
    if before_score is None or after_score is None:
        return 99.9 if turn == chess.WHITE else 0.01
    
    if turn == chess.WHITE:
        loss = max(0, ((before_score -  after_score) * 100))
    else:
        loss = max(0, ((after_score - before_score) * 100))

    accuracy = 103.1668 * math.exp(-0.04354 * loss) - 3.1669

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
                before_info = engine.analyse(board_sim, chess.engine.Limit(time=1, depth=22), multipv=7) #before engine move is played (empty board)

                #get all the moves by the engine
                all_engine_moves = [pv["pv"][0] for pv in before_info] 

                #get the best engine move an convert it to SAN format
                engine_move = all_engine_moves[0]
                engine_san = board_sim.san(engine_move)

                #show the engine move on the board along with other info
                board_sim.push(all_engine_moves[0])
                print(f"No{i+1}. Engine Move: {engine_san} ({all_engine_moves[0]}) \n {board_sim}")

                if board_sim.is_game_over():
                    print("Game Over")
                    continue
                else:
                    beforewdl = before_info[0]["wdl"]

                    before_score = beforewdl.white().expectation()

                    print(beforewdl)
                    print(before_score)  
                    print(beforewdl.white().wins  / 10) 
                    print(beforewdl.white().draws / 10)  
                    print(beforewdl.white().losses / 10)

                print("|———————————————|")

                #convert player move to SAN format and play the mvpe
                player_san = board.san(move)
                board.push(move)
                print(f"Player Move: {player_san} ({move}) \n {board}")
                after_info = engine.analyse(board, chess.engine.Limit(time=1, depth=22))  #after player move is played (e4 board)
                legal_moves = list(board.legal_moves)

                if board.is_game_over():
                    print("Game Over")
                    continue
                else:
                    afterwdl = after_info["wdl"]

                    after_score = afterwdl.white().expectation()

                    print(afterwdl)
                    print(after_score)  
                    print(afterwdl.white().wins / 10) 
                    print(afterwdl.white().draws / 10)  
                    print(afterwdl.white().losses / 10)              

                print("|———————————————|")
                player_move_accuracy = move_accuracy(before_score, after_score, turn)
                print(player_move_accuracy)

                print("~-~-~-~-~-~-~-~-~")
                
except Exception as e:
    print(e)
    print(traceback.format_exc())
finally:
    engine.quit()