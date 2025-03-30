import uuid
import string
import secrets

from sqlalchemy import Column, String, ForeignKey, Text, Integer, DateTime
from sqlalchemy.orm import relationship
from src.database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class ShortLink(Base):
    __tablename__ = "links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_code = Column(String(50), unique=True, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=True)
    user = relationship("User")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    clicks_count = Column(Integer, server_default="0")  # Счетчик переходов
    last_clicked_at = Column(DateTime(timezone=True), nullable=True)  # Дата и время последнего перехода
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Время жизни