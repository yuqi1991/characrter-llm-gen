import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from src.models.data_models import Base  # Import Base from data_models

# Import all models here so that Base knows about them
from src.models.data_models import Character, ApiConfig, Scenario, Dataset, Corpus

logger = logging.getLogger(__name__)


class DatabaseManager:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path="data/character_llm_gen.db"):
        if self._initialized:
            return

        db_url = f"sqlite:///{db_path}"
        logger.info(f"数据库管理器初始化... 数据库路径: {db_url}")

        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        self.session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.Session = scoped_session(self.session_factory)

        self.create_tables()
        self._initialized = True

    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            logger.info("创建数据库表结构...")
            # This will create tables for all models that inherit from Base
            Base.metadata.create_all(self.engine)
            logger.info("数据库表结构创建完成")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}", exc_info=True)

    def get_session(self):
        """Get a new database session."""
        return self.Session()

    def close_session(self):
        """Close the current database session."""
        self.Session.remove()
