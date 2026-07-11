import chess
import math

def game_accuracy(white_move_accuracy, black_move_accuracy):
    white_weights = []
    black_weights = []
    total_moves = len(white_move_accuracy) + len(black_move_accuracy)

    for white_move in white_move_accuracy:
        white_move_weights = 1 + ((8 * math.sqrt(total_moves / 45)) / (1 + math.exp(-12 * (abs(white_move / 100) - 2))))
        white_weights.append(white_move_weights)

    for black_move in black_move_accuracy:
        black_move_weights = 1 + ((8 * math.sqrt(total_moves / 45)) / (1 + math.exp(-12 * (abs(black_move / 100) - 2))))
        black_weights.append(black_move_weights)

    white_game_accuracy = sum(ww * wl for ww, wl in zip(white_weights, white_move_accuracy)) / sum(white_weights)
    black_game_accuracy = sum(bw * bl for bw, bl in zip(black_weights, black_move_accuracy)) / sum(black_weights)

    return white_game_accuracy, black_game_accuracy