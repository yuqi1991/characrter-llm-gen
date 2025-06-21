from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    personality = Column(Text)
    background = Column(Text)
    speaking_style = Column(Text)
    dialogue_examples = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Character(id={self.id}, name='{self.name}')>"


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)  # This will store the prompt template

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Scenario(id={self.id}, name='{self.name}')>"


class ApiConfig(Base):
    __tablename__ = "api_configs"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    api_type = Column(String, nullable=False)  # 'openai', 'google', 'anthropic'
    api_key_encrypted = Column(String, nullable=False)
    base_url_encrypted = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return (
            f"<ApiConfig(id={self.id}, name='{self.name}', api_type='{self.api_type}')>"
        )
