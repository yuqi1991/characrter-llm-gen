from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Table,
    JSON,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
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

    scenarios = relationship(
        "Scenario", back_populates="character", cascade="all, delete-orphan"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Character(id={self.id}, name='{self.name}')>"


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)  # This will store the prompt template

    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    character = relationship("Character", back_populates="scenarios")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("name", "character_id", name="_character_scenario_uc"),
    )

    def __repr__(self):
        return f"<Scenario(id={self.id}, name='{self.name}')>"


class ApiConfig(Base):
    __tablename__ = "api_configs"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    api_type = Column(String, nullable=False)  # 'openai', 'google', 'anthropic'
    api_key_encrypted = Column(String, nullable=False)
    base_url_encrypted = Column(String)

    # New fields for generation parameters
    top_p = Column(Float, default=1.0)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return (
            f"<ApiConfig(id={self.id}, name='{self.name}', api_type='{self.api_type}')>"
        )


# Association table for the many-to-many relationship between Dataset and Scenario
dataset_scenarios_association = Table(
    "dataset_scenarios",
    Base.metadata,
    Column("dataset_id", Integer, ForeignKey("datasets.id"), primary_key=True),
    Column("scenario_id", Integer, ForeignKey("scenarios.id"), primary_key=True),
)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    # Foreign key for the one-to-many relationship with Character
    character_id = Column(Integer, ForeignKey("characters.id"))

    # Relationships
    character = relationship("Character", backref="datasets")
    scenarios = relationship(
        "Scenario", secondary=dataset_scenarios_association, backref="datasets"
    )
    corpus_entries = relationship(
        "Corpus", back_populates="dataset", cascade="all, delete-orphan"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}')>"


# Association table for the many-to-many relationship between Corpus and Scenario
corpus_scenarios_association = Table(
    "corpus_scenarios",
    Base.metadata,
    Column("corpus_id", Integer, ForeignKey("corpus.id"), primary_key=True),
    Column("scenario_id", Integer, ForeignKey("scenarios.id"), primary_key=True),
)


class Corpus(Base):
    __tablename__ = "corpus"

    id = Column(Integer, primary_key=True)
    dialogue = Column(JSON, nullable=False)  # Storing dialogue as JSON

    # Foreign key for the many-to-one relationship with Dataset
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    # Relationships
    dataset = relationship("Dataset", back_populates="corpus_entries")
    scenarios = relationship(
        "Scenario", secondary=corpus_scenarios_association, backref="corpus_entries"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Corpus(id={self.id}, dataset_id={self.dataset_id})>"
