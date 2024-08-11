# utils/loguru_logger.py
import yaml
import sys
from loguru import logger
from typing import Any

from config_data import config


# def setup_logger(config_path: str) -> Type[logger]:
def setup_logger(config_path: str) -> Any:
    """
    Настраивает логгер с использованием конфигурационного файла.
    Аргументы:
        config_path (str): Путь к YAML файлу конфигурации логгера.
    Возвращает:
        logger: Настроенный объект логгера.
    """
    with open(config_path, 'r') as file:
        config_data = yaml.safe_load(file)
    
    logger.remove()  # Удаляем все стандартные обработчики
    for handler in config_data['handlers']:
        if handler['sink'] == 'sys.stdout':
            handler['sink'] = sys.stdout
        logger.add(**handler)
    
    return logger


# Настройка логгера с использованием конфигурационного файла
log = setup_logger(config_path=config.LOGGING_CONF)
