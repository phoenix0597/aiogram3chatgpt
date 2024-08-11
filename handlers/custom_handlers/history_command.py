from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime
from aiogram.types import FSInputFile, InaccessibleMessage
from os import path

from database.requests import get_history_data, get_user
from keyboards.inline.history_buttons import get_history_kb
from config_data.config import BASE_DIR
from utils.common import async_write_file, get_report_header
from utils.actions_decorators import typing_action, upload_document_action

router = Router()


@router.message(Command("history"))
@typing_action(delay=1)
async def cmd_history(message: Message) -> None:
    """
    Обрабатывает команду для получения истории запросов.

    :param message: Сообщение от пользователя.
    """
    await message.answer("Выберите количество запросов или период, запросы за который вы хотите посмотреть:",
                         reply_markup=await get_history_kb())


@router.callback_query(lambda hist: hist.data and hist.data.startswith('history_'))
async def get_history(callback_query: CallbackQuery) -> None:
    """
    Обрабатывает запрос на получение истории запросов.

    :param callback_query: Callback-запрос от пользователя.
    """
    # определяем идентификатор текущего пользователя
    user = await get_user(callback_query.from_user.id)
    if user:
        user_id = user.id
    else:
        raise ValueError("user is None")
    
    # Определяем тип фильтра для запроса: count (кол-во последних запросов) или period (период)
    if isinstance(callback_query.data, str):
        period_or_count_filter = callback_query.data.split("_")[1]  # убираем "history_" из callback_data
    else:
        raise ValueError("callback_query.data is not a string")
    
    responses = await get_history_data(period_or_count_filter, user_id)  # получаем историю запросов из БД
    
    if responses:
        # user = callback_query.from_user
        today_str = datetime.now().strftime("%Y.%m.%d_%H-%M")
        file_name = f"{user.tg_id}_{period_or_count_filter}_{today_str}.txt"
        file_path = path.join(BASE_DIR, "reports", file_name)
        
        # report_header = "История запросов пользователя {} ({}):\n\n".format(user.id, user.username or "N/A")
        report_header = await get_report_header(user)
        await async_write_file(file_path, report_header)
        
        num = 1
        for response in responses:
            
            request_and_response, model_name = response[0], response[1]
            
            hist_record = (f"Запись #{num}.\n\n"
                           f"Модель ИИ:\n{'-' * 20}\n{model_name}\n\n"
                           f"Общее количество токенов:\n{'-' * 20}\n{request_and_response.total_token_quantity}\n\n"
                           f"Запрос:\n{'-' * 20}\n{request_and_response.request}\n\n"
                           f"Ответ:\n{'-' * 20}\n{request_and_response.answer}\n\n\n\n\n"
                           )
            
            await async_write_file(file_path, hist_record)
            num += 1
            
        @upload_document_action(delay=3)
        async def send_file(callback_q: CallbackQuery) -> None:
            mess = callback_q.message
            if mess is not None and not isinstance(mess, InaccessibleMessage):
                await mess.answer_document(FSInputFile(file_path), caption=report_header)
            # await callback_q.message.answer_document(FSInputFile(file_path), caption=report_header)
            
        await send_file(callback_query)
    else:
        # Добавляем декоратор для отправки сообщения о пустой истории
        @typing_action(delay=1)
        async def send_empty_history(mess: Message) -> None:
            await mess.answer("Ваша история запросов пока пуста")
        
        message = callback_query.message
        if message is not None and not isinstance(message, InaccessibleMessage):
            await send_empty_history(message)
        else:
            await callback_query.answer("Не удалось отправить сообщение.")
    
    await callback_query.answer()
