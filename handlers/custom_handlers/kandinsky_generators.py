from aiogram.types import BufferedInputFile
from aiogram.types import Message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from io import BytesIO
from PIL import Image
import base64

from api.kandinsky_generators import Text2ImageAPI
from states import main_states as st
import config_data.config as config
from utils.actions_decorators import typing_action, upload_photo_action

router = Router()


@router.message(F.text == "Сгенерировать \nизображение 🖼")
@typing_action(delay=1)
async def cmd_generate_image(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду для начала генерации изображения.
    Устанавливает состояние FSM для генерации изображения и запрашивает у пользователя ввод.
    Args:
        message (Message): Сообщение от пользователя.
        state (FSMContext): Контекст состояния FSM.
    """
    await state.set_state(st.MainStates.generating_image_state)
    await message.answer('Введите ваш запрос')


@router.message(st.MainStates.generating_image_state)
@typing_action(delay=1)
async def send_photo(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает запрос пользователя для генерации изображения и отправляет сгенерированное изображение.
    Устанавливает состояние FSM для обработки, использует API для генерации изображения и отправляет результат
    пользователю.
    Args:
        message (Message): Сообщение от пользователя.
        state (FSMContext): Контекст состояния FSM.
    """
    await state.set_state(st.MainStates.processing_state)
    api = Text2ImageAPI(url=config.FUSIONBRAIN_URL,
                        api_key=config.FUSIONBRAIN_API_KEY,
                        secret_key=config.FUSIONBRAIN_SECRET_KEY)

    model_id: int = await api.get_model()
    await message.answer(config.WAIT_MESSAGE_AFTER_COMMAND + config.WAIT_MESSAGE_AFTER_COMMAND_IMG)
    uuid: str = await api.generate(message.text, model_id)
    
    # бывает, что Kandinsky API не отдает даже uuid, предусмотрим этот случай
    if uuid is None:
        await message.answer(
            """
            Ошибка: Сервер не смог обработать ваш запрос (возможно, из-за большой нагруженности).
            Попробуйте еще раз. Если ошибка будет повторяться, попробуйте позже или обратитесь к разработчику."
            """
        )
        await state.clear()
        return
    
    # # Ожидание завершения генерации, получаем ответ в виде данных Base64
    images_base64_string: list[str] = await api.check_generation(uuid)
    
    if images_base64_string is None:
        await message.answer("Ошибка: не удалось сгенерировать изображение. Попробуйте еще раз.")
        await state.clear()
        return
    
    # Декодирование данных Base64
    images_base64_data: bytes = base64.b64decode(images_base64_string[0])
    
    # Создание объекта BytesIO
    image_stream: BytesIO = BytesIO(images_base64_data)
    
    # Открытие изображения с помощью PIL для проверки
    image: Image.Image = Image.open(image_stream)
    image.show()  # Отобразим изображение локально (в режиме разработки)
    
    # Перемотать BytesIO объект на начало
    image_stream.seek(0)
    
    # Создание объекта BufferedInputFile
    input_file: BufferedInputFile = BufferedInputFile(image_stream.read(), filename="generated_image.png")

    # Отправляем изображение в чат
    print(f"\nЗапрос на генерацию изображения: {message.text}\n")  # for debugging
    
    # Добавляем декоратор для отправки фото
    @upload_photo_action(delay=3)
    async def send_image(mess: Message, photo: BufferedInputFile) -> None:
        """
        Отправляет сгенерированное изображение в ответ на сообщение пользователя.
        Args:
            mess (Message): Сообщение от пользователя.
            photo (BufferedInputFile): Сгенерированное изображение для отправки.
        """
        await mess.answer_photo(photo=photo)
    
    await send_image(message, input_file)

    await state.clear()
