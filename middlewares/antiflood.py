import asyncio
from typing import Callable, Dict, Awaitable, Any
from aiogram import BaseMiddleware

from aiogram.types import Message, TelegramObject
from cachetools import TTLCache


class AntiFloodMiddleware(BaseMiddleware):
    """
    Промежуточное ПО (middleware) для предотвращения флуда в Telegram боте.
    Ограничивает минимальный интервал между обработкой сообщений от одного пользователя.

    Атрибуты:
        cache_limits (TTLCache): Кэш с временем жизни для ограничения сообщений.
        time_to_live (int): Время жизни записей в кэше (в секундах).
    """

    def __init__(self, time_to_live: int = 3):
        """
        Инициализирует промежуточное ПО с заданным временем жизни для кэша.

        Параметры:
            time_to_live (int): Время жизни записей в кэше в секундах. По умолчанию 3 секунды.
        """
        self.cache_limits: TTLCache[int, None] = TTLCache(maxsize=100, ttl=time_to_live)
        self.time_to_live: int = time_to_live
    
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        """
        Вызывается при обработке каждого сообщения.

        Параметры:
            handler (Callable[[Message, Dict[str, Any]], Awaitable[Any]]): Следующий обработчик в цепочке.
            event (Message): Сообщение от пользователя.
            data (Dict[str, Any]): Дополнительные данные обработчика.

        Возвращает:
            Any: Результат выполнения следующего обработчика или None, если сообщение заблокировано из-за флуда.
        """
        if not isinstance(event, Message):
            return await handler(event, data)
        
        if event.from_user is None:
            return await handler(event, data)
        
        user_id: int = event.from_user.id
        
        if user_id in self.cache_limits:
            answer_message: Message = await event.answer(
                text="Минимальный интервал между запросами ограничен, прошу немного подождать..."
            )
            
            # Ждем время жизни кэша
            await asyncio.sleep(self.time_to_live)
            
            # Удаляем сообщение-ответ
            await answer_message.delete()
            
            # Удаляем исходное сообщение пользователя
            await event.delete()
            return
        
        self.cache_limits[event.from_user.id] = None
        return await handler(event, data)
