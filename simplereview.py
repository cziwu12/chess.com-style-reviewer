import chess
import chess.pgn
import chess.engine 
from chess.engine import Cp, Mate
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

white_move_accuracy = []
black_move_accuracy = []

#check centipawn or mate 
def ismate(info):
    score = info["score"].pov(chess.WHITE)

    if score.is_mate():
        return {
            "type": "mate",
            "mate": score.mate(),
            "cp": None
        }
    else:
        return {
            "type": "cp",
            "mate": None,
            "cp": score.score()
        }
    
def move_accuracy(before_expectation_score, after_expectation_score, turn):
    if before_expectation_score is None or after_expectation_score is None:
        return 99.99 if turn == chess.WHITE else 0.01
    
    loss = max(0, before_expectation_score - after_expectation_score) * 100 if turn == chess.WHITE else max(0, after_expectation_score - before_expectation_score) * 100

    accuracy = 103.1668 * math.exp(-0.04354 * loss) - 3.1669
    accuracy = max(0, min(100, accuracy))

    white_move_accuracy.append(accuracy) if turn == chess.WHITE else black_move_accuracy.append(accuracy)
    
    return round(max(0, accuracy), 2)

def game_accuracy(white_move_accuracy, black_move_accuracy):
    print(white_move_accuracy)
    print(black_move_accuracy)
    white_weights = []
    black_weights = []
    total_moves = len(white_move_accuracy) + len(black_move_accuracy)

    for white_move in white_move_accuracy:
        white_move_weights = 1 + ((8 * math.sqrt(total_moves / 45)) / (1 + math.exp(-12 * (abs(white_move / 100) - 0.2))))
        white_weights.append(white_move_weights)

    for black_move in black_move_accuracy:
        black_move_weights = 1 + ((8 * math.sqrt(total_moves / 45)) / (1 + math.exp(-12 * (abs(black_move / 100) - 0.2))))
        black_weights.append(black_move_weights)

    white_game_accuracy = sum(ww * wl for ww, wl in zip(white_weights, white_move_accuracy)) / sum(white_weights)
    black_game_accuracy = sum(bw * bl for bw, bl in zip(black_weights, black_move_accuracy)) / sum(black_weights)

    return white_game_accuracy, black_game_accuracy

#calculates the loss/gain of prepetual attack from both sides
def static_exchange_eval(board, target_square):
    gainscore = []
    turn = board.turn

    white_attackers = list(board.attackers(chess.WHITE, target_square))
    black_attackers = list(board.attackers(chess.BLACK, target_square))

    #find the attacks in the initial position
    initial_attackers = white_attackers if turn == chess.WHITE else black_attackers
    if not initial_attackers:
        return 0 
    
    #find the target square location
    target_piece_square =  board.piece_at(target_square)
    if  not target_piece_square:
        return 0
    
    #get the target piece cp
    current_piece_value = PIECE_VALUES[target_piece_square.piece_type]
    gainscore.append(current_piece_value)

    #run perpetual attack in copy board
    sim_board = board.copy()

    while True:
        #check attackers per move, if there's no more attackers, break
        attackers =  sim_board.attackers(turn, target_square)
        if not attackers:
            break

        #check for the lowest value attacker
        lowest_attacker_square = minimum_attacker_values(sim_board, attackers)
        attacker_piece = sim_board.piece_at(lowest_attacker_square)

        gainscore.append(current_piece_value)

        #move the attacker piece to target square and assign it as the next target piece
        current_piece_value = PIECE_VALUES[attacker_piece.piece_type]

        move = chess.Move(lowest_attacker_square, target_square)
        sim_board.push(move)

        turn = not turn 

    while len(gainscore) > 1:
        #if gainscore is negative, the defender lose cp
        last_gainscore = gainscore.pop()
        gainscore[-1] = gainscore[-1] - max(0, last_gainscore)
    
    return gainscore[0]

#find the square that holds the lowest value attacker
def minimum_attacker_values(board, attackers):
    return min(attackers, key=lambda sq: PIECE_VALUES[board.piece_at(sq).piece_type])

#scans every square and fin hanging pieces 
def find_loses(board):
    loses = {
        "Loose Piece": [],
        "Hanging Piece":  [],
        "En Prise": []
    }

    for square, piece in board.piece_map().items():

        defender_color = piece.color
        attacker_color = not defender_color

        attackers = board.attackers(attacker_color, square)
        defenders = board.attackers(defender_color, square)

        if attackers:
            if not defenders:
                loses["Loose Piece"].append((chess.square_name(square), piece.symbol()))

            else:
                board_sim = board.copy()

                see_score = static_exchange_eval(board_sim, square)

                if board.turn == attacker_color:
                    loses["En Prise"].append((chess.square_name(square), piece.symbol()))
                else:
                    loses["Hanging Piece"].append((chess.square_name(square), piece.symbol()))

    return loses

#classify mate scores/cp/mix and return a classification
def classify_scores(before_info, after_info, turn, playermove, legalmoves, engine_move):
    score1 = before_info["score"].pov(chess.WHITE)
    score2 = after_info["score"].pov(chess.WHITE)

    if score1 is not None and score2 is not None:

        if len(legalmoves) == 1:
            return "Forced"
        elif playermove == engine_move:
            return "Best"
        elif score1.is_mate() and score2.is_mate():
            matescore1 = score1.mate()
            matescore2 = score2.mate()
            matescore_eval = 0
        
            if turn == chess.WHITE:
                matescore_eval = matescore1 - matescore2
            else:
                matescore_eval = matescore2 - matescore1

            if matescore_eval >= 3:
                return "Best"
            elif matescore_eval == 2:
                return "Great"
            elif matescore_eval ==1:
                return "Good"
            elif matescore_eval == 0:
                return "Miss"
            elif matescore_eval == -1:
                return "Inaccuracy"
            elif matescore_eval == -2:
                return "Mistake"
            else:
                return "Blunder"
        elif isinstance(score1, Mate) and isinstance(score2, Cp):
            cpscore = score1.score()

            if cpscore <= 100:
                return "Miss"
            elif cpscore <=200:
                return "Mistake"
            else:
                return "Blunder"
        elif isinstance(score1, Cp) and isinstance(score2, Mate):
            matescore = score2.mate()
            
            if matescore <= 3:
                return "Best"
            elif matescore <= 5:
                return "Great"
            else:
                return "Good"
        else:
            cpscore1 = score1.score()
            cpscore2 = score2.score()
            cpscore_eval = 0

            if turn == chess.WHITE:
                cpscore_eval = cpscore1 - cpscore2
            else:
                cpscore_eval = cpscore2 - cpscore1  

            if cpscore_eval <= 5:
                return "Best"
            elif cpscore_eval <= 10:
                return "Excellent"
            elif cpscore_eval <= 20:
                return "Great"
            elif cpscore_eval <= 50:
                return "Good"
            elif cpscore_eval <= 100:
                return "Inaccuracy"
            elif cpscore_eval <= 300:
                return "Mistake"
            else:
                return "Blunder"

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

                #get the best engine move an convert it to SAN format
                engine_move = before_info["pv"][0]
                engine_san = board_sim.san(engine_move)

                #show the engine move on the board along with other info
                board_sim.push(engine_move)
                print(f"No{i+1}. Engine Move: {engine_san} \n {board_sim}")

                before_wdl = before_info["wdl"].white()
                before_expection_score = before_wdl.expectation()
                
                print(f"WDL Prob: Win: {before_wdl.wins / 10}% | Draw: {before_wdl.draws / 10}% | Loss: {before_wdl.losses / 10}%")

                #formating the score 
                before_score_info = ismate(before_info)
                ply += 1
                if before_score_info["type"] == "mate":
                    print(f"Evaluation Before Move: Mate in {abs(before_score_info["mate"])}")
                else:
                    print(f"Evaluation Before Move: {before_score_info["cp"]/100:+.2f} Ply: {ply}")


                print("|———————————————|")

                #convert player move to SAN format and play the mvpe
                player_san = board.san(move)
                board.push(move)
                print(f"Player Move: {player_san} \n {board}")
                after_info = engine.analyse(board, chess.engine.Limit(time=1, depth=22))  #after player move is played (e4 board)
                legal_moves = list(board.legal_moves)

                if board.is_game_over():
                    if board.is_stalemate:
                        accuracy = 0.5
                    elif turn == chess.WHITE:
                        accuracy = 1.0
                    else:
                        accuracy = 0.0
                else:
                    after_wdl = after_info["wdl"].white()
                    after_expection_score = after_wdl.expectation()
                
                    print(f"WDL Prob: Win: {after_wdl.wins / 10}% | Draw: {after_wdl.draws / 10}% | Loss: {after_wdl.losses / 10}%")               

                #format the score
                after_score_info = ismate(after_info)
                ply += 1
                if after_score_info["type"] == "mate":
                    print(f"Evaluation After Move: Mate in {abs(after_score_info["mate"])}")
                else:
                    print(f"Evaluation After Move: {after_score_info["cp"]/100:+.2f} Ply: {ply}")


                print("|———————————————|")

                #calculating cpl

                classification = classify_scores(before_info, after_info, turn, move, legal_moves, engine_move)

                if before_score_info["type"] == "mate" or after_score_info["type"] == "mate":
                    pass
                else:
                    if turn == chess.WHITE:
                        CPL = max(0, before_score_info["cp"] - after_score_info["cp"]) 
                        turn_name = "White"
                    else:
                        CPL = max(0, after_score_info["cp"] - before_score_info["cp"]) 
                        turn_name = "Black"

                accuracy = move_accuracy(before_expection_score, after_expection_score, turn)

            
                #print CPL, classificationn and engine I move
                print(f"CPL: {CPL / 100}, Classification: {classification})")
                print(f"[Turn: {turn_name}, Hanging pieces: {find_loses(board)}]")
                print(accuracy)
                print("~-~-~-~-~-~-~-~-~")
            
            white_game_accuracy, black_game_accuracy = game_accuracy(white_move_accuracy, black_move_accuracy)
            print(f"White Game Accuracy: {white_game_accuracy}%")
            print(f"Black Game Accuracy: {black_game_accuracy}%")
except Exception as e:
    print(e)
    print(traceback.format_exc())
finally:
    engine.quit()

