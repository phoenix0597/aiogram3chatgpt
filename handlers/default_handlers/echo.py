from aiogram.types import Message
from aiogram import Router
from keyboards.reply import main_kb as kb
from utils.actions_decorators import typing_action

router = Router()


@typing_action(delay=2)
async def reply_to_text(message: Message) -> None:
    """
    Отправляет ответное сообщение с предложением выбрать тип генерации контента.

    :param message: Входящее сообщение от пользователя.
    """
    await message.answer("Пожалуйста, выберите тип генерации контента,\n"
                         "нажав одну из кнопок: \n'Сгенерировать текст' или 'Сгенерировать изображение'",
                         reply_markup=kb.main_kb)


# Эхо-хэндлер, обрабатывающий текстовые сообщения, не подпадающие под какие-либо фильтры
@router.message()
async def bot_echo(message: Message) -> None:
    """
    Эхо-хэндлер, обрабатывающий текстовые сообщения, не подпадающие под какие-либо фильтры.

    :param message: Входящее сообщение от пользователя.
    """
    await reply_to_text(message)
