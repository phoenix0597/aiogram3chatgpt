import os
import json
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from typing import List

from utils import bot_loader
from handlers.custom_handlers import (gpt_generators, kandinsky_generators, history_command,
                                      high_low_commands, processing_state_handling)
from handlers.default_handlers import start, help, echo
from middlewares.antiflood import AntiFloodMiddleware
from middlewares.check_old_requests import UpdateTimeValidationMiddleware
from database.models import async_create_all
from config_data import config
from utils.loguru_logger import log

# Инициализируем бота
bot = bot_loader.bot
dp = Dispatcher()

# Подключаем мидлвейры
dp.message.middleware(AntiFloodMiddleware())
dp.message.middleware(UpdateTimeValidationMiddleware())

# Регистрируем роутеры обработчиков
dp.include_routers(
    processing_state_handling.router,
    gpt_generators.router,
    kandinsky_generators.router,
    history_command.router,
    high_low_commands.router,
    start.router,
    help.router,
    echo.router,
)


async def main() -> None:
    """Запускает бота"""
    await async_create_all()
    await async_set_bot_commands(current_bot=bot)
    
    # очищаем состояния и удаляем необработанные до запуска функции main() апдейты
    await bot.delete_webhook(drop_pending_updates=True)
    
    # для устранения ошибок соединения с сервером Telegram
    try:
        await dp.start_polling(bot, request_timeout=60)  # Увеличим значение таймаута
        log.info("Bot started successfully")
    
    finally:
        await bot.session.close()
    
    # Периодическое обновление команд кнопки "Меню" (каждые 5 минут)
    await asyncio.create_task(async_periodic_command_updater(interval=300))


async def get_username_by_id(tg_id: int, current_bot: Bot) -> str | None:
    """
    Возвращает имя пользователя по его Telegram ID.

    :param tg_id: Telegram ID пользователя.
    :param current_bot: Экземпляр бота.
    :return: Имя пользователя или None, если не удалось получить.
    """
    try:
        user = await current_bot.get_chat(tg_id)
        return user.username
    except Exception as e:
        # print(f"Error retrieving username for {tg_id}: {e}")
        log.error(f"Error retrieving username for {tg_id}: {e}")
        return None


async def async_set_bot_commands(current_bot: Bot) -> None:
    """
    Устанавливает команды бота на основе файла bot_commands.json.
    :param current_bot: Экземпляр бота.
    """
    
    # Путь к JSON-файлу
    json_path = os.path.join(config.CONFIG_DIR, 'bot_commands.json')
    
    with open(json_path, 'r', encoding='utf-8') as file:
        bot_commands = json.load(file)
    
    commands: List[BotCommand] = [BotCommand(**cmd) for cmd in bot_commands]
    await current_bot.set_my_commands(commands)


async def async_periodic_command_updater(interval: int = 300) -> None:
    """
    Периодически обновляет команды бота, восстанавливая кнопку "Меню" в левом нижнем углу,
    иногда исчезающую в случае ошибки (соединения и прочих).

    :param interval: Интервал времени в секундах между обновлениями команд.
    """
    while True:
        try:
            await async_set_bot_commands(bot)
            log.info("Bot commands have been updated")
        except Exception as e:
            log.error(f"Error updating bot commands: {repr(e)}")
        
        await asyncio.sleep(interval)


async def main_loop() -> None:
    """
    Основной цикл работы бота с обработкой исключений и перезапуском.
    :return: None
    """
    
    retry_delay = 1  # начальная задержка в секундах
    max_delay = 300  # максимальная задержка

    while True:
        try:
            log.info("Starting the main loop main_loop()")  # Добавляем отладочное сообщение
            await main()
            retry_delay = 1  # сброс задержки после успешного выполнения
        except (KeyboardInterrupt, SystemExit, asyncio.CancelledError) as e:
            log.info(f"The bot's work is completed by the user's command ({repr(e)})")
            await bot.session.close()
            break
        except ConnectionError as e:
            log.error(f"Bot stopped with connection error: {repr(e)}")
            await asyncio.sleep(retry_delay)
            retry_delay = min(max_delay, retry_delay * 2)  # удвоение задержки
        except Exception as e:
            log.error(f"Bot stopped with error: {repr(e)}")
            await asyncio.sleep(retry_delay)
            retry_delay = min(max_delay, retry_delay * 2)  # удвоение задержки
    

if __name__ == '__main__':
    with log.catch():
        asyncio.run(main_loop())
