import json
import os
from aiogram.types import Message
from aiogram import Router
from aiogram.filters import Command

from config_data.config import CONFIG_DIR
from utils.actions_decorators import typing_action

router = Router()


@router.message(Command("help"))
@typing_action(delay=1)
async def bot_help(message: Message) -> None:
    """
    Отправляет список доступных команд и их описания.

    :param message: Входящее сообщение от пользователя.
    """
    # Получаем путь к директории, в которой находится скрипт
    config_dir = CONFIG_DIR

    # Путь к JSON-файлу
    json_path = os.path.join(config_dir, 'bot_commands.json')

    with open(json_path, 'r', encoding='utf-8') as file:
        bot_commands = json.load(file)

    # text = [f"/{command} - {desk}" for command, desk in DEFAULT_COMMANDS]
    text = [f"/{cmd['command']}\t\t\t\t\t - {cmd['description']}" for cmd in bot_commands]

    await message.answer("\n".join(text))
