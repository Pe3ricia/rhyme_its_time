from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # Telegram user ID
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="waiting")  # waiting, active, finished
    created_at = Column(DateTime, default=datetime.utcnow)
    max_lines_per_player = Column(Integer, default=2)
    current_turn = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    order_index = Column(Integer, nullable=False)

    user = relationship("User")
    game = relationship("GameSession")

class Line(Base):
    __tablename__ = "lines"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)