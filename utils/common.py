import os
import aiofiles
import asyncio

from database.models import User as DBUser


async def async_write_file(file_path: str, data: str) -> None:
    """
    Функция асинхронной записи данных в файл

    :param file_path: путь к файлу
    :param data: данные для записи
    :return: None
    """
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    async with aiofiles.open(file_path, 'a', encoding='utf-8') as file:
        await file.write(data)


async def async_sleep(seconds: float) -> None:
    """
    Асинхронно приостанавливает выполнение программы на заданное количество секунд.
    
    :param seconds: Количество секунд для приостановки.
    """
    
    await asyncio.sleep(seconds)


async def get_report_header(user: DBUser) -> str:
    """
    Формирует заголовок отчета для пользователя.
    
    :param user: Объект пользователя Telegram.
    :return: Заголовок отчета.
    """
    
    return f"История запросов пользователя {user.tg_id} ({user.username or 'username is N/A'})\n\n"
