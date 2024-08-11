import asyncio
from aiogram.types import Message, User
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from typing import Optional

from api.gpt_generators import gpt_text  # , gpt_image
from states import main_states as st
from database.requests import put_txt_gpt_data_to_db
import config_data.config as config
from utils.actions_decorators import typing_action
from utils.loguru_logger import log  # Импорт настроенного логгера

router = Router()


@router.message(F.text == "Сгенерировать \nтекст 📄")
@typing_action(delay=1)
async def cmd_generate_text(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду для начала генерации текста.

    :param message: Сообщение от пользователя.
    :param state: Контекст состояния FSM.
    """
    try:
        log.debug("The user started generating text")
        await state.set_state(st.MainStates.await_input_for_gen_text)
        await message.answer('Введите ваш запрос')
        user_id = message.from_user.id if message.from_user else 'неизвестный пользователь'
        log.info(f"User {user_id} set the state {st.MainStates.await_input_for_gen_text}")
        # log.info(f"Пользователь {message.from_user.id} установил состояние {st.MainStates.await_input_for_gen_text}")

    except Exception as err:
        log.error(f"Error setting state for text generation: {repr(err)}")
        await message.answer("Произошла ошибка, попробуйте позже.")


@router.message(st.MainStates.await_input_for_gen_text)
@typing_action(delay=1)
async def send_result(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает запрос пользователя для генерации текста и отправляет результат.

    :param message: Сообщение от пользователя.
    :param state: Контекст состояния FSM.
    """
    user: Optional[User] = message.from_user
    if not user:
        await message.answer("Не удалось определить пользователя.")
        log.error("Failed to determine user.")
        return
    
    log.debug("Processing user input to generate text")
    await state.set_state(st.MainStates.processing_state)
    log.info(f"Request to generate text from {user.username}: {message.text}")
    
    await message.answer(config.WAIT_MESSAGE_AFTER_COMMAND + config.WAIT_MESSAGE_AFTER_COMMAND_TXT)
    if message.text is None:
        await message.answer("Запрос не должен быть пустым.")
        await state.clear()
        return
    
    response = await gpt_text(message.text)
    if not response or not response.choices or not response.choices[0].message:
        await message.answer("Не удалось получить ответ от GPT.")
        await state.clear()
        return
    
    if response.choices[0].message.content and response.usage:
        # Получение названия модели
        model_name = response.model
        log.debug(f"Model {model_name} used {response.usage.total_tokens} tokens for response.")
    
        await put_txt_gpt_data_to_db(request=message.text,
                                     answer=response.choices[0].message.content,
                                     total_token_quantity=response.usage.total_tokens,
                                     model_name=model_name,
                                     user_id=user.id,
                                     )
    if response.usage:
        log.info(f"Data is saved in the database for the user {user.id}")
        log.debug(f"Costs per request (in tokens): \n"
                  f"Prompt tokens: {response.usage.prompt_tokens}, \n"
                  f"Completion tokens: {response.usage.completion_tokens}, \n"
                  f"Total tokens: {response.usage.total_tokens}\n"
                  f"Generated response: {response.choices[0].message.content}\n")
    
    # Отправляем полученный ответ в чат
    # await message.answer(response.choices[0].message.content)
    if response.choices[0].message.content is not None:
        await message.answer(response.choices[0].message.content)
    else:
        log.error("There is no response text to send to the user.")
        await message.answer("Не удалось сформировать ответ.")
        await state.clear()
        return
    
    log.info(f"Reply sent to user {user.username}")
    
    await asyncio.sleep(3)  # дадим время на получение пользователем ответа и потом сбросим состояние
    await state.clear()
    log.debug(f"State reset for user {user.id}")

# -------------------------------------------------------------------------------------------------#
# These handlers are workable but API they use is not free, so we use free Kandinsky API instead   #
# -------------------------------------------------------------------------------------------------#
# @router.message(F.text == "Сгенерировать изображение 🖼")
# async def cmd_generate_image(message: Message, state: FSMContext):
#     await message.answer('Введите ваш запрос')
#     await state.set_state(st.MainStates.await_input_for_gen_text)


# @router.message(st.MainStates.generating_image_state)
# async def send_result(message: Message, state: FSMContext):
#     await state.set_state(st.MainStates.processing_state)
#     await message.answer('Ответ:')
#     response = await gpt_image(message.text)
#     await message.answer_photo(photo=response.data[0].url)
#     await state.clear()
# --------------------------------------------------------------------------------------------------#
