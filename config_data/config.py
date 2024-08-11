import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

ENV = os.getenv("ENV")

if ENV == "dev":
    BOT_TOKEN = os.getenv("BOT_TOKEN_DEV")
elif ENV == "feat":
    BOT_TOKEN = os.getenv("BOT_TOKEN_FEATURE")

PROXY_API_BASE_URL = os.getenv("PROXY_API_BASE_URL")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")

OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")

# Kandinsky configs
FUSIONBRAIN_URL = os.getenv("FUSIONBRAIN_URL")
FUSIONBRAIN_API_KEY = os.getenv("FUSIONBRAIN_API_KEY")
FUSIONBRAIN_SECRET_KEY = os.getenv("FUSIONBRAIN_SECRET_KEY")

# Constants
WAIT_MESSAGE_AFTER_COMMAND = 'Запрос получен, дождитесь пожалуйста ответа...\n'
WAIT_MESSAGE_AFTER_COMMAND_TXT = 'Генерация ответа может занять до нескольких секунд.'
WAIT_MESSAGE_AFTER_COMMAND_IMG = ('Генерация изображения может занять до 2-х минут, '
                                  'в зависимости от нагруженности сервера.')

# database configs
SQLALCHEMY_URL = os.getenv("DATABASE_URL")
SQLALCHEMY_ECHO = False  # True

# buttons for command /history
HISTORY_BUTTONS = {"Последние 5 запросов": "last5",
                   "Последние 10 запросов": "last10",
                   "Все за последнюю неделю": "7",
                   "Все за последний месяц": "30",
                   "За все время": "all"
                   }

# buttons for commands /high and /low
HIGH_LOW_BUTTONS = {"Вывести 5 запросов": ("high_5", "low_5"),
                    "Вывести 10 запросов": ("high_10", "low_10"),
                    "Укажите сколько вывести запросов": "custom"
                    }

# CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = Path(__file__).parent
BASE_DIR = Path(__file__).parent.parent


# LOGGING_CONF = os.path.join(BASE_DIR, 'config_data', 'logging.conf')
LOGGING_CONF = os.path.join(BASE_DIR, 'config_data', 'loguru_config.yaml')
