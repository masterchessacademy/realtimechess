import os
import asyncio
import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import chess
from .db import DB
from .engine import EngineWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
STOCKFISH_PATH = os.environ.get('STOCKFISH_PATH', '/usr/games/stockfish')
ANALYSIS_TIME = float(os.environ.get('ANALYSIS_TIME', '0.25'))

db = DB('games.db')
engine = EngineWrapper(STOCKFISH_PATH)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome to Master Chess Academy Bot! Use /play to start a new game.')

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    board = chess.Board()
    db.save_game(chat_id, board.fen(), pgn='')
    await update.message.reply_text('New game created. You play White. Make your move with /move e2e4')

async def move_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.message.reply_text('Usage: /move e2e4  (also accepts e2 e4)')
        return
    uci = ''.join(args).strip()
    record = db.load_game(chat_id)
    if not record:
        await update.message.reply_text('No active game. Start one with /play')
        return
    board = chess.Board(record['fen'])
    try:
        move = chess.Move.from_uci(uci)
    except Exception:
        await update.message.reply_text('Invalid UCI move format. Example: e2e4')
        return
    if move not in board.legal_moves:
        await update.message.reply_text('Illegal move. Try again.')
        return
    board.push(move)
    # engine response
    try:
        engine_move = engine.play(board, time_limit=ANALYSIS_TIME)
        board.push(engine_move)
    except Exception as e:
        logger.exception('Engine failed to play: %s', e)
        await update.message.reply_text('Engine error. Please try later.')
        return
    db.save_game(chat_id, board.fen(), pgn=board.epd())
    await update.message.reply_text(f'You played: {uci}\nBot played: {engine_move}\n\nBoard:\n{board}\n\nFEN:\n{board.fen()}')

async def board_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    record = db.load_game(chat_id)
    if not record:
        await update.message.reply_text('No active game. Use /play to start.')
        return
    board = chess.Board(record['fen'])
    await update.message.reply_text(f'Board:\n{board}\n\nFEN:\n{board.fen()}')

async def pgn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    record = db.load_game(chat_id)
    if not record:
        await update.message.reply_text('No active game. Use /play to start.')
        return
    board = chess.Board(record['fen'])
    # produce simple PGN header-less
    pgn = board.accept(chess.pgn.StringExporter(headers=False, variations=False, comments=False))
    await update.message.reply_text(f'PGN:\n{pgn}')

def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit('TELEGRAM_TOKEN env var is required.')
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('play', play))
    app.add_handler(CommandHandler('move', move_cmd))
    app.add_handler(CommandHandler('board', board_cmd))
    app.add_handler(CommandHandler('pgn', pgn_cmd))

    logger.info('Bot starting...')
    app.run_polling()

if __name__ == '__main__':
    main()
