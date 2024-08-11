from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from config_data import config

if config.BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN is not defined")

default = DefaultBotProperties(parse_mode='Markdown')
bot = Bot(token=config.BOT_TOKEN, default=default)
