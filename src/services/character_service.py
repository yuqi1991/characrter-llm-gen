import logging
from contextlib import contextmanager
from src.database.database_manager import DatabaseManager
from src.models.data_models import Character

logger = logging.getLogger(__name__)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库会话期间发生错误: {e}", exc_info=True)
        raise
    finally:
        session.close()


def get_all_characters():
    """获取所有角色卡的列表"""
    with session_scope() as session:
        characters = session.query(Character).all()
        logger.info(f"成功获取 {len(characters)} 个角色")
        return characters


def get_all_character_names():
    """获取所有角色卡的名称列表"""
    with session_scope() as session:
        results = session.query(Character.name).order_by(Character.name).all()
        logger.info(f"成功获取 {len(results)} 个角色名称")
        return [r[0] for r in results]


def get_character_by_name(name: str):
    """通过名称获取角色卡, 返回一个字典"""
    if not name:
        return None
    with session_scope() as session:
        char = session.query(Character).filter_by(name=name).first()
        if char:
            return {
                "id": char.id,
                "name": char.name,
                "description": char.description,
                "personality": char.personality,
                "background": char.background,
                "speaking_style": char.speaking_style,
                "dialogue_examples": char.dialogue_examples,
            }
        return None


def save_character(id: int = None, **kwargs):
    """创建或更新角色卡"""
    with session_scope() as session:
        char_name = kwargs.get("name")
        if not char_name:
            raise ValueError("角色名称不能为空")

        if id:
            character = session.query(Character).filter_by(id=id).first()
            if character:
                logger.info(f"正在更新角色: {char_name}")
                existing_char = (
                    session.query(Character)
                    .filter(Character.name == char_name, Character.id != id)
                    .first()
                )
                if existing_char:
                    raise ValueError(f"角色名称 '{char_name}' 已存在。")
                for key, value in kwargs.items():
                    setattr(character, key, value)
                return

        existing_char = session.query(Character).filter_by(name=char_name).first()
        if existing_char:
            raise ValueError(f"角色名称 '{char_name}' 已存在。")

        logger.info(f"正在创建新角色: {char_name}")
        new_character = Character(**kwargs)
        session.add(new_character)
        session.flush()


def delete_character_by_name(name: str):
    """通过名称删除角色卡"""
    with session_scope() as session:
        character = session.query(Character).filter_by(name=name).first()
        if character:
            logger.info(f"正在删除角色: {name}")
            session.delete(character)
            return True
        logger.warning(f"尝试删除一个不存在的角色: {name}")
        return False
