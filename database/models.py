from sqlalchemy import BigInteger, ForeignKey, String, DateTime, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config_data.config import SQLALCHEMY_URL, SQLALCHEMY_ECHO  # (True)
from utils.loguru_logger import log


# Проверка на None и установка значения по умолчанию
if SQLALCHEMY_URL is None:
    raise ValueError("SQLALCHEMY_URL не должно быть None")

async_engine = create_async_engine(url=SQLALCHEMY_URL, echo=SQLALCHEMY_ECHO)
# "postgresql+asyncpg://user:password@host:port/dbname[?key=value&key=value...]"

async_session = async_sessionmaker(async_engine)


class Base(DeclarativeBase, AsyncAttrs):
    pass


class User(Base):
    """
    Модель пользователя.

    :param id: Первичный ключ.
    :param tg_id: Telegram ID пользователя.
    :param username: Имя пользователя.
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, tg_id={self.tg_id}, username='{self.username}')>"


class AIModel(Base):
    """
    Модель AI.

    :param id: Первичный ключ.
    :param name: Название модели.
    """
    __tablename__ = "ai_models"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    
    def __repr__(self) -> str:
        return f"<AIModel(id={self.id}, name='{self.name}')>"
    

class RequestAndResponse(Base):
    """
    Модель запроса и ответа.

    :param id: Первичный ключ.
    :param request: Текст запроса.
    :param answer: Текст ответа.
    :param total_token_quantity: Общее количество токенов.
    :param model_id: ID модели.
    :param user_id: ID пользователя.
    :param requests_date: Дата запроса.
    """
    __tablename__ = "requests_to_ai"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    request: Mapped[str] = mapped_column(String(100000))
    answer: Mapped[str] = mapped_column(String(20000))
    total_token_quantity: Mapped[int] = mapped_column()
    model_id: Mapped[int] = mapped_column(ForeignKey("ai_models.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    requests_date: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    
    def __repr__(self) -> str:
        return (f"<RequestAndResponse(id={self.id}, \nrequest='{self.request}', \nanswer='{self.answer}', "
                f"\ntotal_token_quantity={self.total_token_quantity}, \nmodel_id={self.model_id}, "
                f"\nuser_id={self.user_id}, \nrequests_date={self.requests_date})>")


async def async_create_all() -> None:
    """
    Создание схемы БД.
    :return:
    """
    log.info("Trying to create a database schema")
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("The database schema has been successfully created")
    except Exception as e:
        log.exception(f"Error creating database schema: {str(e)}")
        raise
