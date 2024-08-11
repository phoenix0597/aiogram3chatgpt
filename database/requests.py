from sqlalchemy import select, func
from sqlalchemy.engine import Result
from sqlalchemy.sql.selectable import Select
from database.models import User, RequestAndResponse, AIModel, async_session
from datetime import timedelta, datetime
from typing import Optional, Tuple, Sequence

from utils.loguru_logger import log


async def set_user(tg_id: int, username: Optional[str] = None) -> None:
    """
    Устанавливает пользователя в базе данных.
    Если пользователь с указанным tg_id не существует, создает нового пользователя.

    Args:
        tg_id (int): Telegram ID пользователя.
        username (Optional[str]): Имя пользователя (по умолчанию None).
    """
    log.info(f"Trying to set user with tg_id={tg_id}, username={username}")
    async with async_session() as session:
        # подключаемся к БД и ищем в ней текущего пользователя
        user = await get_user(tg_id)
        
        if not user:
            log.info(f"Creating new user with tg_id={tg_id}, username={username}")
            try:
                session.add(User(tg_id=tg_id, username=username))
                await session.commit()
            except Exception as e:
                log.error(f"Error while creating new user: {e}")
                await session.rollback()
                # await session.commit()
            # session.add(User(tg_id=tg_id, username=username))
            log.info(f"A new user has been created with tg_id={tg_id}, username={username}")
            return
        else:
            log.info(f"User with tg_id={tg_id}, username={username} already exists in the database")
            return


async def get_user(tg_id: int) -> Optional[User]:
    """
    Получает пользователя из базы данных по его Telegram ID.

    Args:
        tg_id (int): Telegram ID пользователя.

    Returns:
        Optional[User]: Объект пользователя или None, если пользователь не найден.
    """
    log.debug(f"User's with tg_id={tg_id} request")
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            log.info(f"User found: {user}")
        else:
            log.warning(f"User with tg_id={tg_id} can't be found")
        return user


async def ensure_model_exists(model_name: str) -> int:
    """
    Убеждается, что модель существует в базе данных, или создает новую модель.

    Args:
        model_name (str): Название модели.

    Returns:
        int: ID модели.
    """
    log.debug(f"Checking the existence of a model named {model_name}")
    async with async_session() as session:
        # Проверяем, существует ли модель
        model = await session.scalar(select(AIModel).where(AIModel.name == model_name))
        if not model:
            # Добавляем модель, если не существует
            new_model = AIModel(name=model_name)
            session.add(new_model)
            await session.commit()
            log.info(f"A new model with the name {model_name} и id={new_model.id} has been created")
            return new_model.id
        
        log.info(f"The model {model_name} with id={model.id} already exists in the database")
        return model.id


async def ensure_user_exists(user_id: int, username: Optional[str] = None) -> int:
    """
    Убеждается, что пользователь существует в базе данных, или создает нового пользователя.

    Args:
        user_id (int): Telegram ID пользователя.
        username (Optional[str]): Имя пользователя (по умолчанию None).
    Returns:
        int: ID пользователя.
    Raises:
        ValueError: Если пользователь не найден и не задан username.
    """
    log.debug(f"Checking user with id={user_id} existence in the database")
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        if not user and username is not None:
            new_user = User(tg_id=user_id, username=username)
            session.add(new_user)
            await session.commit()
            log.info(f"A new user with id={new_user.id} и username={username} has been created")
            return new_user.id
        elif user:
            log.info(f"User with id={user.id} already exists in the database")
            return user.id
        else:
            log.error(f"User with id={user_id} not found and username is not set")
            raise ValueError


async def put_txt_gpt_data_to_db(request: str, answer: str, total_token_quantity: int,
                                 model_name: str, user_id: int) -> None:
    """
    Сохраняет данные запроса и ответа GPT в базу данных.

    Args:
        request (str): Текст запроса.
        answer (str): Текст ответа.
        total_token_quantity (int): Общее количество токенов.
        model_name (str): Название модели.
        user_id (int): ID пользователя.
    """
    log.info(
        f"Saving request and response data from GPT: request='{request}', model_name='{model_name}', user_id={user_id}")
    try:
        # Убеждаемся, что модель существует или создаем её
        model_id = await ensure_model_exists(model_name)
        
        # Убеждаемся, что пользователь существует или создаем его
        user_id = await ensure_user_exists(user_id)
        log.info(f"Trying to save request and response data from GPT model with id={model_id} "
                 f"for the user with id={user_id}")
        async with async_session() as session:
            session.add(RequestAndResponse(
                request=request,
                answer=answer,
                total_token_quantity=total_token_quantity,
                model_id=model_id,
                user_id=user_id,
                requests_date=func.now()
            ))
            await session.commit()
            log.info(
                f"Request and response data from GPT successfully saved to the database for the user with id={user_id}"
            )
    
    except Exception as e:
        log.error(f"Error saving GPT request and response data: {str(e)}")
        raise


async def get_base_query(user_id: int) -> Select[Tuple[RequestAndResponse, str]]:
    """
    Формирует базовый запрос для получения данных запросов и ответов пользователя.

    Args:
        user_id (int): ID пользователя.
    Returns:
        select: Базовый запрос SQLAlchemy.
    """
    log.debug(f"Generating a basic request for a user with id={user_id}")
    query = (
        select(RequestAndResponse, AIModel.name.label('model_name'))
        .join(AIModel, AIModel.id == RequestAndResponse.model_id)
        .where(RequestAndResponse.user_id == user_id)
    )
    return query


async def get_history_data(period_or_count_filter: str,
                           user_id: int) -> Sequence[Tuple[RequestAndResponse, str]]:
    """
    Получает историю данных запросов и ответов пользователя за указанный период или количество записей.

    Args:
        period_or_count_filter (str): Фильтр по периоду ("days7", "days30") или количеству записей ("last7", "last30").
        user_id (int): ID пользователя.
    Returns:
        Sequence[Tuple[RequestAndResponse, str]]: Список кортежей, содержащих объекты RequestAndResponse и название модели.
    """
    log.info(f"Retrieving data history with a filter {period_or_count_filter} for user with id={user_id}")
    # Формируем базовый запрос, к которому, при необходимости, будем применять фильтры
    query = await get_base_query(user_id)
    
    if period_or_count_filter.startswith("days"):  # "7" или "30" (дней)
        # Определяем временной период для запроса и добавляем его в запрос
        period = int(period_or_count_filter[4:])
        
        # определяем значения по умолчанию начало и конца периода запроса
        now = datetime.now()
        start_date = now - timedelta(days=period)
        end_date = now
        
        # добавляем к базовому запросу фильтр по количеству дней
        query = query.where(
            (RequestAndResponse.requests_date >= start_date) & (RequestAndResponse.requests_date <= end_date)
        )
        log.debug(f"Filter by period applied: {start_date} - {end_date}")
    
    if period_or_count_filter.startswith("last"):  # last7 или last30
        count = int(period_or_count_filter[4:])
        
        # добавляем к базовому запросу ограничение по количеству записей
        query = query.order_by(RequestAndResponse.requests_date.desc()).limit(count)
        log.debug(f"Filter by number of records applied: {count}")
    
    # Выполняем запрос и обрабатываем результаты
    async with async_session() as session:
        try:
            response: Result[Tuple[RequestAndResponse, str]] = await session.execute(query)
            responses = [tuple(row) for row in response.all()]  # Преобразуем Row в кортеж
            
            log.info(f"{len(responses)} records for user with id={user_id} received")
        except Exception as e:
            log.error(f"An error occurred while retrieving data: {str(e)}")
            raise
    
    return responses


async def get_high_low_data(high_or_low_filter: str,
                            count: int,
                            user_id: int) -> Sequence[Tuple[RequestAndResponse, str]]:
    """
    Получает данные с наибольшим или наименьшим количеством токенов для пользователя.

    Args:
        high_or_low_filter (str): Фильтр по количеству токенов ("high5", "low5").
        count (int): Количество записей.
        user_id (int): ID пользователя.

    Returns:
        Sequence[Tuple[RequestAndResponse, str]]: Последовательность кортежей,
        содержащих объекты RequestAndResponse и название модели.
    """
    log.info(f"Retrieving data with a filter {high_or_low_filter} and quantity {count} for user with id={user_id}")
    # Формируем базовый запрос, к которому, при необходимости, будем применять фильтры
    query = await get_base_query(user_id)
    
    if high_or_low_filter.startswith("high"):  # high_5, high_10 или custom
        query = query.order_by(RequestAndResponse.total_token_quantity.desc()).limit(count)
        log.debug(f"Filter by number of tokens applied (high): {count}")
    
    if high_or_low_filter.startswith("low"):  # low_5, low_10 или custom
        query = query.order_by(RequestAndResponse.total_token_quantity.asc()).limit(count)
        log.debug(f"Filter by number of tokens applied (low): {count}")
    
    # Выполняем запрос и обрабатываем результаты
    async with async_session() as session:
        try:
            response: Result[Tuple[RequestAndResponse, str]] = await session.execute(query)
            responses = [tuple(row) for row in response.all()]  # Преобразуем Row в кортеж
            
            log.info(
                f"{len(responses)} records with filter {high_or_low_filter} received for user with id={user_id}")
        except Exception as e:
            log.error(f"An error occurred while retrieving filtered data {high_or_low_filter}: {str(e)}")
            raise
    
    return responses
