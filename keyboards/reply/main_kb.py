from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Сгенерировать \nтекст 📄"),
            KeyboardButton(text="Сгенерировать \nизображение 🖼"),
        ],
    ], resize_keyboard=True, one_time_keyboard=True)
