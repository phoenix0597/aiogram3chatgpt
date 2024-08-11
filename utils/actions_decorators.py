import asyncio
from functools import wraps
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatAction
from typing import Callable, Union, TypeVar, Coroutine, Any


# Определяем переменную типа для декорируемой функции
F = TypeVar('F', bound=Callable[..., Coroutine[Any, Any, Any]])


def typing_action(delay: int = 1) -> Callable[[F], F]:
    """
    Декоратор для отправки статуса "печатает..." в чат перед выполнением функции.

    Параметры:
    - delay (int): Задержка в секундах между отправкой статуса и выполнением функции.
    Возвращает:
    - Callable[[F], F]: Декоратор для функции.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(message: Message, *args: Any, **kwargs: Any) -> Any:
            bot = message.bot
            if bot is None:
                raise ValueError("Bot instance is not available in the message.")

            await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            # await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
            await asyncio.sleep(delay)
            result = await func(message, *args, **kwargs)
            return result
        
        return wrapper
    
    return decorator


def upload_photo_action(delay: int = 3) -> Callable:
    """
    Декоратор для отправки статуса "загружает фото..." в чат перед выполнением функции.

    Параметры:
    - delay (int): Задержка в секундах между отправкой статуса и выполнением функции.
    Возвращает:
    - Callable[[F], F]: Декоратор для функции.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(message: Message, *args: Any, **kwargs: Any) -> Any:
            bot = message.bot
            if bot is None:
                raise ValueError("Bot instance is not available in the message.")
            # await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
            await asyncio.sleep(delay)
            result = await func(message, *args, **kwargs)
            return result
        
        return wrapper
    
    return decorator


def upload_document_action(delay: int = 3) -> Callable[[F], F]:
    """
    Декоратор для отправки статуса "загружает документ..." в чат перед выполнением функции.

    Параметры:
    - delay (int): Задержка в секундах между отправкой статуса и выполнением функции.
    Возвращает:
    - Callable[[F], F]: Декоратор для функции.
    """
    # def decorator(func: Callable[[Union[Message, CallbackQuery]], Awaitable[None]]) -> Callable:
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(arg: Union[Message, CallbackQuery], *args: Any, **kwargs: Any) -> Any:
            if isinstance(arg, CallbackQuery):
                message = arg.message
                if message is None or message.bot is None:
                    raise ValueError("Bot instance is not available in the callback query message.")
                await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
            elif isinstance(arg, Message):
                bot = arg.bot
                if bot is None:
                    raise ValueError("Bot instance is not available in the message.")
                await bot.send_chat_action(arg.chat.id, ChatAction.UPLOAD_DOCUMENT)
            await asyncio.sleep(delay)
            result = await func(arg, *args, **kwargs)
            return result
        return wrapper
    
    return decorator
