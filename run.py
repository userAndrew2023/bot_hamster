from bot import bot
from db.db import init_db
from handlers import start_handler

init_db()
bot.infinity_polling(timeout=60)
