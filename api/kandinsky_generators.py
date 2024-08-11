import json
import time
import requests
from typing import Any


class Text2ImageAPI:
    """
    Класс для взаимодействия с API генерации изображений на основе текста.

    :param url: URL API.
    :param api_key: Ключ API.
    :param secret_key: Секретный ключ API.
    """
    def __init__(self, url: str, api_key: str, secret_key: str):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    async def get_model(self) -> int:
        """
        Получает ID модели для генерации изображений.

        :return: ID модели.
        """
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        # for debugging
        print(data)
        if isinstance(data, list) and len(data) > 0 and 'id' in data[0] and isinstance(data[0]['id'], int):
            # returns id of model Kandinsky 3.1 (the only one which currently supports connection via API)
            return data[0]['id']
        raise ValueError("No valid model ID found in response")

    async def generate(self, prompt: str, model: int, images: int = 1,
                       width: int = 1024, height: int = 1024,
                       attempts: int = 10, delay: int = 10) -> tuple[str | None, ...] | None:
        """
        Генерирует изображение на основе текстового запроса.

        :param prompt: Текстовый запрос для генерации изображения.
        :param model: ID модели для генерации.
        :param images: Количество изображений для генерации.
        :param width: Ширина изображения.
        :param height: Высота изображения.
        :param attempts: Количество попыток генерации.
        :param delay: Задержка между попытками.
        :return: UUID запроса на генерацию или None, если генерация не удалась.
        """
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        # data = {
        #     'model_id': (None, model),
        #     'params': (None, json.dumps(params), 'application/json')
        # }
        
        data = {
            'model_id': (None, str(model)),
            'params': (None, json.dumps(params), 'application/json')
        }
        
        # for debugging
        while data.get('uuid') is None and attempts > 0:
            # response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
            response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
            data = response.json()
            print('Response from generate() function (data):', data)
            attempts -= 1
            time.sleep(delay)
        
        return data.get('uuid')

    async def check_generation(self, request_id: str, attempts: int = 15, delay: int = 10) -> Any:
        """
        Проверяет статус генерации изображения.

        :param request_id: UUID запроса на генерацию.
        :param attempts: Количество попыток проверки.
        :param delay: Задержка между попытками.
        :return: Данные изображения или None, если генерация не завершена.
        """
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data.get('status') == 'DONE':
                return data.get('images')
            
            attempts -= 1
            time.sleep(delay)
            delay += 2
        # Если генерация не завершена, возвращаем None
        return None
