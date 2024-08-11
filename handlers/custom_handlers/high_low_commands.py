from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.types import FSInputFile
from os import path
from typing import Sequence

from database.requests import get_high_low_data, get_user
from keyboards.inline.high_low_buttons import get_high_low_kb
from config_data.config import BASE_DIR, WAIT_MESSAGE_AFTER_COMMAND
from utils.common import async_write_file, get_report_header
from utils.actions_decorators import (typing_action, upload_document_action)
from states import main_states as st
from utils.loguru_logger import log
from database.models import RequestAndResponse

router = Router()


async def get_high_low_message(comm: str, message: Message) -> None:
    """
    Формирует текст сообщения, в зависимости от полученной от пользователя команды - "high" или "low"
    и отправляет его пользователю.

    :param comm: Команда для обработки.
    :param message: Сообщение от пользователя.
    """
    insertion, custom_num = "", ""
    if comm == "/high":
        insertion = "максимальной"
        custom_num = "high_custom_num"
    elif comm == "/low":
        insertion = "минимальной"
        custom_num = "low_custom_num"
    else:
        log.error(f"\n\nНеизвестная команда: {comm}\n\n")
    await message.answer(f"Выберите количество запросов с {insertion} стоимостью, "
                         f"отчет по которым вы хотите получить:",
                         reply_markup=await get_high_low_kb(custom_num, comm[1:]))


@router.message(Command("high"))
@typing_action(delay=1)
async def cmd_high(message: Message) -> None:
    """
    Обрабатывает команду для получения запросов с наибольшей стоимостью.

    :param message: Сообщение от пользователя.
    """
    await get_high_low_message('/high', message)


@router.message(Command("low"))
@typing_action(delay=1)
async def cmd_low(message: Message) -> None:
    """
    Обрабатывает команду для получения запросов с наименьшей стоимостью.

    :param message: Сообщение от пользователя.
    """
    await get_high_low_message('/low', message)


@typing_action(delay=1)
async def cmd_set_custom_num(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду для установки пользовательского количества запросов.

    :param message: Сообщение от пользователя.
    :param state: Контекст состояния FSM.
    """
    await message.answer("Введите количество запросов:")
    await state.set_state(st.HighLowStates.waiting_for_custom_num_state)


# Обработчик пользовательского ввода в состоянии waiting_for_custom_num_state
@router.message(st.HighLowStates.waiting_for_custom_num_state)
async def process_custom_number(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает пользовательский ввод для установки количества запросов.

    :param message: Сообщение от пользователя.
    :param state: Контекст состояния FSM.
    """
    try:
        # Преобразуем сообщение в целое число
        if message.text is None:
            raise ValueError("Текст сообщения не должен быть пустым.")
        num_requests = int(message.text)
        
        if num_requests < 0:
            raise ValueError("Число должно быть положительным.")
        
        # Сохраняем количество запросов в состояние
        await state.update_data(custom_num=num_requests)
        user_data = await state.get_data()
        high_or_low_filter = user_data.get("high_or_low_filter")
        await state.clear()
        
        if not isinstance(high_or_low_filter, str):
            await message.answer("Внутренняя ошибка: тип фильтра не определён.")
            return
        
        await get_high_low_history_with_custom_num(message, high_or_low_filter, num_requests)
    
    except ValueError:
        await message.answer("Количество запросов должно быть целым числом.")


async def get_high_low_history_with_custom_num(message: Message,
                                               high_or_low_filter: str,
                                               count: int) -> None:
    """
    Получает историю запросов с наибольшей или наименьшей стоимостью с пользовательским количеством.

    :param message: Сообщение от пользователя.
    :param high_or_low_filter: Фильтр по количеству токенов ("high" или "low").
    :param count: Количество запросов.
    """
    if message.from_user is None:
        log.error("Отправитель сообщения не определен.")
        return
    
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Пользователь не найден в базе данных.")
        return
    
    user_id = user.id
    
    await message.answer(WAIT_MESSAGE_AFTER_COMMAND)
    
    responses = await get_high_low_data(high_or_low_filter, count, user_id)
    
    if not responses:
        await message.answer("Нет данных для отображения.")
        return
    
    report_header = await get_report_header(user)
    report = await get_report(responses, report_header)
    
    today_str = datetime.now().strftime("%Y.%m.%d_%H-%M_%S")
    file_name = f"{user.tg_id}_{high_or_low_filter}{count}_{today_str}.txt"
    report_file_path = path.join(BASE_DIR, "reports", file_name)
    await async_write_file(report_file_path, report)
    
    report_file = FSInputFile(report_file_path)
    
    # @upload_document_action_with_message(delay=3)
    @upload_document_action(delay=3)
    async def send_file(mess: Message) -> None:
        await mess.answer_document(report_file, caption=report_header)
    
    await send_file(message)


@router.callback_query(lambda hist: hist.data.startswith('high_') or hist.data.startswith('low_'))
async def get_high_low_history(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает запрос на получение истории запросов с наибольшей или наименьшей стоимостью.

    :param callback_query: Callback-запрос от пользователя.
    :param state: Контекст состояния FSM.
    """
    if not isinstance(callback_query.message, Message):
        log.error("Невозможно получить доступ к сообщению для отправки документа.")
        return
    
    # определяем идентификатор текущего пользователя
    user = await get_user(callback_query.from_user.id)
    if not user:
        await callback_query.answer("Пользователь не найден в базе данных.")
        return
    
    user_id = user.id
    
    # Определяем тип фильтра (high или low), а также количество запросов (count)
    if not isinstance(callback_query.data, str):
        await callback_query.answer("Внутренняя ошибка: тип фильтра не определён.")
        log.error("Тип фильтра не определён.")
        return
    high_or_low_filter, count_str = callback_query.data.split("_", 1)
    log.info(f"Filter (high_or_low_filter): {high_or_low_filter} "
             f"and number of requests (count): {count_str} defined")
    
    if count_str == "custom_num":
        await state.set_state(st.HighLowStates.waiting_for_custom_num_state)
        await cmd_set_custom_num(callback_query.message, state)
        await state.update_data(high_or_low_filter=high_or_low_filter)
        await callback_query.answer()
        return
    
    try:
        count = int(count_str)
    except ValueError:
        user_data = await state.get_data()
        count = user_data.get("custom_num", 0)
        high_or_low_filter = user_data.get("high_or_low_filter", "")
        
        if count is None:
            await callback_query.message.answer("The number of requests must be an integer.")
            await callback_query.answer()
            return
    
    await callback_query.answer(WAIT_MESSAGE_AFTER_COMMAND)
    responses = await get_high_low_data(high_or_low_filter, count, user_id)  # получаем историю запросов из БД
    
    if responses:
        
        today_str = datetime.now().strftime("%Y.%m.%d_%H-%M")
        file_name = f"{user.tg_id}_{high_or_low_filter}{count}_{today_str}.txt"
        report_file_path = path.join(BASE_DIR, "reports", file_name)
        
        report_header = await get_report_header(user)
        report = await get_report(responses, report_header)
        
        await async_write_file(report_file_path, report)
        
        report_file = FSInputFile(report_file_path)
        
        @upload_document_action(delay=3)
        async def send_file(callback_q: CallbackQuery) -> None:
            mess = callback_q.message
            if not isinstance(mess, Message):
                log.error("Cannot access message to send document.")
                return
            
            await mess.answer_document(report_file, caption=report_header)
        
        await send_file(callback_query)
        await callback_query.message.delete()
    
    else:
        # Добавляем декоратор для отправки сообщения о пустой истории
        @typing_action(delay=1)
        async def send_empty_history(message: Message) -> None:
            await message.answer("Ваша история запросов пока пуста")
        
        if not isinstance(callback_query.message, Message):
            await callback_query.answer("Невозможно получить доступ к сообщению.")
            return
        await send_empty_history(callback_query.message)
    
    await callback_query.answer()


# async def get_report(responses: List[Any], report_header: str) -> str:
async def get_report(responses: Sequence[tuple[RequestAndResponse, str]], report_header: str) -> str:
    """
    Формирует отчет на основе данных запросов и ответов.

    :param responses: Последовательность кортежей,
    содержащих объекты RequestAndResponse и название модели.
    :param report_header: Заголовок отчета.
    :return: Сформированный отчет в виде строки.
    """
    report = report_header
    report += "\n\n".join(
        [
            f"Запись #{num}\n\n"
            f"Дата запроса:\n{resp[0].requests_date}\n\n"
            f"Модель ИИ:\n{resp[1]}\n\n"
            f"Общее количество токенов:\n{resp[0].total_token_quantity}\n"
            f"Запрос:\n{'-' * 20}\n{resp[0].request}\n"
            f"Ответ:\n{'-' * 20}\n{resp[0].answer}\n\n"
            for num, resp in enumerate(responses, start=1)
        ]
    )
    return report
