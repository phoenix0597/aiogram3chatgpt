from aiogram.filters.state import StatesGroup, State


class MainStates(StatesGroup):
    """
    Состояния для основного процесса работы бота.
    """
    await_input_for_gen_text = State()
    generating_image_state = State()
    processing_state = State()
    

class HighLowStates(StatesGroup):
    """
    Состояния для обработки команд high и low.
    """
    waiting_for_custom_num_state = State()
