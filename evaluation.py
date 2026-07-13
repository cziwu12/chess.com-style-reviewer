import chess
from chess.engine import Cp, Mate
import math

def score(score):
    score = score.white()

    if score.is_mate():
        return score.mate()
    else:
        return score.score()
    
def wdl(wdl):
    wdl = wdl.white()
    expectation_score =  wdl.expectation()

    win_prob = wdl.wins / 10
    draw_prob = wdl.draws / 10
    loss_prob = wdl.losses / 10
    return expectation_score, win_prob, draw_prob, loss_prob

def classification(before_score, after_score, playermove, engine_move, turn, legal_moves):
    before_score_w = before_score.white()
    after_score_w = after_score.white()

    if len(legal_moves) == 1:
        return "Forced"
    elif playermove == engine_move:
        return "Best"
    elif before_score.is_mate() and after_score.is_mate():
        matescore1 = before_score_w.mate()
        matescore2 = after_score_w.mate()
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
    elif before_score.is_mate() :
        centipawn_score = before_score_w.score()
        if centipawn_score <= 100:
            #and isinstance(after_score, Cp)
            return "Miss"
        elif centipawn_score <=200:
            return "Mistake"
        else:
            return "Blunder"
    elif after_score.is_mate():
        matescore = after_score_w.mate()
        #isinstance(before_score, Cp) and 
        
        if matescore <= 3:
            return "Best"
        elif matescore <= 5:
            return "Great"
        else:
            return "Good"
    else:
        cpscore1 = before_score_w.score()
        cpscore2 = after_score_w.score()
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
            
def move_accuracy(before_expectation_score, after_expectation_score, turn):
    if before_expectation_score is None or after_expectation_score is None:
        return 99.99 if turn == chess.WHITE else 0.01
    
    loss = max(0, before_expectation_score - after_expectation_score) * 100 if turn == chess.WHITE else max(0, after_expectation_score - before_expectation_score) * 100

    accuracy = 103.1668 * math.exp(-0.04354 * loss) - 3.1669
    accuracy = max(0, min(100, accuracy))
    
    return round(max(0, accuracy), 2)

def wdl_gameover(board, turn):
    if board.is_stalemate():
        win, draw, loss = 0.0, 100.0, 0.0
    elif turn == chess.WHITE:
        win, draw, loss = 100.0, 0.0, 0.0
    else: 
        win, draw, loss = 0.0, 0.0, 100.0
    return win, draw, loss

def cpl(before_cp, after_cp, turn):
    if turn == chess.WHITE:
        CPL = before_cp - after_cp
    else:
        CPL = after_cp - before_cp
    return CPL