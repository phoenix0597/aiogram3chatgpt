from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup, ReplyKeyboardMarkup)
from config_data.config import HISTORY_BUTTONS


async def get_history_kb() -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
    Асинхронная функция для создания клавиатуры с кнопками истории.
    Клавиатура создается на основе данных из HISTORY_BUTTONS и возвращается
    в виде объекта InlineKeyboardMarkup.
    Returns:
        InlineKeyboardMarkup: Объект клавиатуры с кнопками истории.
    """
    history_kb = InlineKeyboardBuilder()
    
    for key, val in HISTORY_BUTTONS.items():
        # 'history_last5', 'history_last10', 'history_7', 'history_30', 'history_all'
        history_kb.add(InlineKeyboardButton(text=key, callback_data="history_" + str(val)))
    
    return history_kb.adjust(2).as_markup()
