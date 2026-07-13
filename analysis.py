import chess.engine

engine = chess.engine.SimpleEngine.popen_uci(r"C:\Users\notcz\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe")

engine.configure({"UCI_ShowWDL": True})

def analyse_game(board, move):
        turn = board.turn

        board_sim = board.copy()
        before_info = engine.analyse(board_sim, chess.engine.Limit(time=1, depth=22)) 

        engine_move = before_info["pv"][0]
        engine_san = board_sim.san(engine_move)

        board_sim.push(engine_move)
        before_board_fen = board_sim.fen()

        player_san = board.san(move)
        board.push(move)
        player_board_fen = board.fen()

        after_info = engine.analyse(board, chess.engine.Limit(time=1, depth=22)) 
        legal_moves = list(board.legal_moves)

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

