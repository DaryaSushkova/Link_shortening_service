from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from src.database import Base
from uuid import uuid4


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    # Прочие поля уже есть в базовой таблице
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)