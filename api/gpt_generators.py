from openai import AsyncClient
from openai.types import ImagesResponse
from openai.types.chat import ChatCompletion

from config_data import config

client = AsyncClient(
    api_key=config.PROXY_API_KEY,
    base_url=config.PROXY_API_BASE_URL,
)


async def gpt_text(req: str) -> ChatCompletion:
    """
    Асинхронная функция для получения текстового ответа от модели GPT-3.5.
    Args:
        req (str): Входной запрос пользователя.
    Returns:
        dict: Ответ модели в формате словаря.
    """
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": req,
            }
        ],
        model="gpt-3.5-turbo",
    )

    return chat_completion
    # return {"choices": [choice["message"]["content"] for choice in chat_completion["choices"]]}


# This function is workable but API it uses is not free, so we use free Kandinsky API instead
async def gpt_image(req: str) -> ImagesResponse:
    """
    Асинхронная функция для генерации изображения с использованием модели DALL-E-3.
    Args:
        req (str): Входной запрос пользователя для генерации изображения.
    Returns:
        ImagesResponse: Ответ модели с изображением.
    """
    response = await client.images.generate(
        model="dall-e-3",
        prompt=req,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return response
