import enum
from sqlalchemy import Column, String, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseMixin
from app.database import Base

class SessionType(str, enum.Enum):
    manager = "manager"
    customer = "customer"

class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"

class ChatSession(Base, BaseMixin):
    __tablename__ = "chat_sessions"
    
    session_type = Column(SAEnum(SessionType), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    session_metadata = Column(JSON, nullable=True)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

class ChatMessage(Base, BaseMixin):
    __tablename__ = "chat_messages"
    
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(SAEnum(MessageRole), nullable=False)
    content = Column(String, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    tool_call_id = Column(String, nullable=True)
    
    session = relationship("ChatSession", back_populates="messages")
