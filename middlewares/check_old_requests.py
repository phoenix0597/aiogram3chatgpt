from datetime import datetime, timedelta, timezone
from aiogram import BaseMiddleware
from aiogram.types import Update, TelegramObject, Message
from typing import Callable, Dict, Awaitable, Any


# Middleware апдейт на просроченность (позволяет избегать ошибок обработки устаревших апдейтов)
class UpdateTimeValidationMiddleware(BaseMiddleware):
    """
    Промежуточное ПО для проверки времени обновления.
    Этот middleware позволяет избегать ошибок обработки устаревших обновлений,
    пропуская обработку апдейтов, которые старше заданного временного порога.
    """
    
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        """
        Вызывается при обработке каждого апдейта.

        Параметры:
            handler: Callable - следующий обработчик в цепочке обработки.
            event: Union[Update, Message, CallbackQuery] - событие, которое нужно обработать.
            data: Dict[str, Union[str, datetime]] - дополнительные данные обработчика.

        Возвращает:
            None, если апдейт слишком старый и его следует пропустить.
            Awaitable[None], результат выполнения следующего обработчика в цепочке.
        """
        
        time_stamp: datetime | None = None
        
        if isinstance(event, Update):
            # Проверяем, является ли событие сообщением и имеет ли оно дату
            if event.message and isinstance(event.message, Message):
                time_stamp = event.message.date
            # Проверяем, является ли событие callback_query и имеет ли оно дату
            elif (event.callback_query and event.callback_query.message
                  and isinstance(event.callback_query.message, Message)):
                time_stamp = event.callback_query.message.date
        
        if time_stamp:
            # current_time = datetime.utcnow()
            current_time: datetime = datetime.now(timezone.utc)
            update_time = time_stamp
            if current_time - update_time > timedelta(seconds=30):
                print("Update is too old and will be skipped")
                return
        
        return await handler(event, data)
