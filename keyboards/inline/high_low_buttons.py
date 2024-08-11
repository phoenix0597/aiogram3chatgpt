from aiogram.utils.keyboard import (InlineKeyboardBuilder, InlineKeyboardButton,
                                    InlineKeyboardMarkup, ReplyKeyboardMarkup)
from config_data.config import HIGH_LOW_BUTTONS


async def get_high_low_kb(custom_num: str,
                          command: str | None = None) -> InlineKeyboardMarkup | ReplyKeyboardMarkup:
    """
        Создает и возвращает инлайн-клавиатуру для Telegram бота с кнопками для выбора количества запросов.
        Функция генерирует динамические коллбэк-данные для кнопок на основе переданного параметра command
        и пользовательского числа custom_num. Кнопки размещаются в два столбца.

        Args:
            custom_num (str): Строка, представляющая пользовательское число, которое будет использовано
                              в коллбэк-данных одной из кнопок.
            command (str, optional): Команда, определяющая, какие коллбэк-данные будут использоваться для кнопок.
                                     Может быть "high" или "low". По умолчанию None.
        Returns:
            InlineKeyboardMarkup: Объект инлайн-клавиатуры aiogram, содержащий сгенерированные кнопки.
        Пример:
            >>> from aiogram import types
            >>> async def command_handler(message: types.Message):
            ...     markup = await get_high_low_kb("15", "high")
            ...     await message.answer("Выберите опцию:", reply_markup=markup)
        """
    high_low_index = None
    if command == "high":
        high_low_index = 0
    elif command == "low":
        high_low_index = 1
    high_low_kb = InlineKeyboardBuilder()
    
    # добавим кнопки с коллбэками, которые сформируем в зависимости от параметра command
    # ('high_5', 'low_5', 'high_10', 'low_10', f'high_{custom_num}' или f'low_{custom_num}')
    for key, val in HIGH_LOW_BUTTONS.items():
        if key == "Укажите сколько вывести запросов":
            callback_string = custom_num
        else:
            # Проверяем, что high_low_index не None перед использованием его как индекса
            if high_low_index is not None:
                callback_string = str(val[high_low_index])
            else:
                # Обработка случая, когда high_low_index равен None
                raise ValueError("high_low_index is None")
        
        high_low_kb.add(InlineKeyboardButton(text=key, callback_data=callback_string))
    
    return high_low_kb.adjust(2).as_markup()
