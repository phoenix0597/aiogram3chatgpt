from aiogram.types import Message
from aiogram import Router
from aiogram.filters import CommandStart
from keyboards.reply import main_kb as kb
from aiogram.fsm.context import FSMContext
from database.requests import set_user
from utils.actions_decorators import typing_action

router = Router()


@router.message(CommandStart())
@typing_action(delay=1)
async def bot_start(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /start, очищает состояние и регистрирует пользователя.

    :param message: Входящее сообщение от пользователя.
    :param state: Контекст состояния FSM.
    """
    await state.clear()
    
    # Получаем имя и фамилию пользователя из сообщения
    user = message.from_user
    if not user:
        await message.answer("Не удалось определить пользователя.")
        return
    username = user.username
    
    # await set_user(message.from_user.id)
    # Передаем tg_id и username в функцию set_user
    if user:
        await set_user(tg_id=user.id, username=username)
    else:
        raise ValueError("user is None")
    
    await message.reply(
        text="""
Приветствую, мастер! 🎨
Добро пожаловать в мир бесконечных возможностей!
Я — твой ИИ-ассистент, готовый воплотить в жизнь любые текстовые и визуальные фантазии.
Просто отправь мне запрос, и я отвечу на него, сгенерирую для тебя уникальные тексты
или удивительные картинки. Давай начнем это увлекательное путешествие вместе!!
""",
        reply_markup=kb.main_kb)
