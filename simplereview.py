import chess
import chess.pgn
import chess.engine 
from chess.engine import Cp, Mate
import traceback

engine = chess.engine.SimpleEngine.popen_uci(r"C:\Users\notcz\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe")

PIECE_VALUES = {
    chess.PAWN: 100,      
    chess.KNIGHT: 300,    
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 100000
}

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
    
#check if player move is in engine moves
def in_all_engine_moves(move, all_engine_moves):
    if move in all_engine_moves:
        return f"Engine's #{all_engine_moves.index(move) + 1} Move"
    else:
        pass

def cp_to_win_prob(before_score_info, after_score_info, turn):
    before_score = before_score_info["cp"]
    after_score = after_score_info["cp"]
    if before_score is None or after_score is None:
        return 0
    
    before_pawn_score = round(before_score / 100, 3)
    after_pawn_score = round(after_score / 100, 3)

    before_win_prob = round(1 / (1 + 10**(-before_pawn_score / 4)) * 100, 2)
    after_win_prob = round(1 / (1 + 10**(-after_pawn_score / 4)) * 100, 2)

    if turn == chess.WHITE:
        return f"{before_win_prob}%", f"{after_win_prob}%", "white" 
    else:
        return f"{100 - before_win_prob}%", f"{100 - after_win_prob}%", "black"

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
def classify_scores(before_info, after_info, turn, playermove, legalmoves, all_engine_moves):
    score1 = before_info[0]["score"].pov(chess.WHITE)
    score2 = after_info["score"].pov(chess.WHITE)

    if score1 is not None and score2 is not None:

        if len(legalmoves) == 1:
            return "Forced"
        elif playermove == all_engine_moves[0]:
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

            for i, move in enumerate(game.mainline_moves()):
                moving_side = board.turn

                #analysing initial board and get the engine move
                board_sim = board.copy()
                before_info = engine.analyse(board_sim, chess.engine.Limit(time=1, depth=10), multipv=7) #before engine move is played (empty board)

                #get all the moves by the engine
                all_engine_moves = [pv["pv"][0] for pv in before_info] 

                #get the best engine move an convert it to SAN format
                engine_move = all_engine_moves[0]
                engine_san = board_sim.san(engine_move)

                #show the engine move on the board along with other info
                board_sim.push(all_engine_moves[0])
                print(f"No{i+1}. Engine Move: {engine_san} ({all_engine_moves[0]}) \n {board_sim}")

                #formating the score 
                before_score_info = ismate(before_info[0])
                if before_score_info["type"] == "mate":
                    print(f"Evaluation Before Move: Mate in {abs(before_score_info["mate"])}")
                else:
                    print(f"Evaluation Before Move: {before_score_info["cp"]/100:+.2f}")

                print("|———————————————|")

                #convert player move to SAN format and play the mvpe
                player_san = board.san(move)
                board.push(move)
                print(f"Player Move: {player_san} ({move}) \n {board}")
                after_info = engine.analyse(board, chess.engine.Limit(time=1, depth=10))  #after player move is played (e4 board)
                legal_moves = list(board.legal_moves)

                #format the score
                after_score_info = ismate(after_info)
                if after_score_info["type"] == "mate":
                    print(f"Evaluation After Move: Mate in {abs(after_score_info["mate"])}")
                else:
                    print(f"Evaluation After Move: {after_score_info["cp"]/100:+.2f}")

                print("|———————————————|")

                #calculating cpl

                classification = classify_scores(before_info, after_info, moving_side, move, legal_moves, all_engine_moves)

                if before_score_info["type"] == "mate" or after_score_info["type"] == "mate":
                    pass
                else:
                    if moving_side == chess.WHITE:
                        CPL = max(0, before_score_info["cp"] - after_score_info["cp"]) 
                        turn = "White"
                    else:
                        CPL = max(0, after_score_info["cp"] - before_score_info["cp"]) 
                        turn = "Black"
            
                #print CPL, classificationn and engine I move
                print(f"CPL: {CPL / 100}, Classification: {classification}, {in_all_engine_moves(move, all_engine_moves)}")
                print(f"[Turn: {turn}, Hanging pieces: {find_loses(board)}]")
                print(f"Win prob: {cp_to_win_prob(before_score_info, after_score_info, moving_side)}")
                print("~-~-~-~-~-~-~-~-~")
                
except Exception as e:
    print(e)
    print(traceback.format_exc())
finally:
    engine.quit()

