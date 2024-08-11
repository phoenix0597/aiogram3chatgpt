from aiogram.types import Message
from aiogram import Router, F
from states import main_states as st

router = Router()


@router.message(st.MainStates.processing_state, F.text != "/start")
async def when_is_processing_state(message: Message) -> None:
    """
    Обработчик сообщений в состоянии `processing_state`, если текст сообщения не равен "/start".

    Args:
        message (Message): Входящее сообщение от пользователя.
    Returns:
        None
    """
    await message.answer("Операция в процессе. Пожалуйста, подождите...")
