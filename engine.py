import chess
import chess.engine
import os

class EngineWrapper:
    def __init__(self, path='/usr/games/stockfish'):
        self.path = path
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'Stockfish binary not found at {self.path}')
        # we will create engine on demand per-play to avoid long-lived process issues in container

    def play(self, board: chess.Board, time_limit=0.25):
        # time_limit in seconds (float)
        with chess.engine.SimpleEngine.popen_uci(self.path) as eng:
            limit = chess.engine.Limit(time=time_limit)
            result = eng.play(board, limit)
            return result.move
