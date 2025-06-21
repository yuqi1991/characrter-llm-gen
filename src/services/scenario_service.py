import logging
from contextlib import contextmanager
from src.database.database_manager import DatabaseManager
from src.models.data_models import Scenario

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


def get_all_scenarios():
    """获取所有场景，返回字典列表"""
    with session_scope() as session:
        scenarios = session.query(Scenario).order_by(Scenario.name).all()
        logger.info(f"成功获取 {len(scenarios)} 个场景")
        return [
            {"id": s.id, "name": s.name, "description": s.description}
            for s in scenarios
        ]


def get_all_scenarios_for_display():
    """获取所有场景，用于在Dataframe中显示"""
    with session_scope() as session:
        scenarios = (
            session.query(Scenario.name, Scenario.description)
            .order_by(Scenario.name)
            .all()
        )
        logger.info(f"成功获取 {len(scenarios)} 个场景")
        return scenarios if scenarios else []


def save_scenario(
    original_name: str = None, new_name: str = None, description: str = None
):
    """创建或更新场景。"""
    if not new_name:
        raise ValueError("场景名称不能为空")

    with session_scope() as session:
        # 如果提供了 original_name，说明是更新操作
        if original_name and original_name != new_name:
            # 检查新名称是否与其它场景冲突
            existing_with_new_name = (
                session.query(Scenario).filter_by(name=new_name).first()
            )
            if existing_with_new_name:
                raise ValueError(f"场景名称 '{new_name}' 已存在。")

        scenario = None
        if original_name:
            scenario = session.query(Scenario).filter_by(name=original_name).first()

        # 如果找到了场景，则更新
        if scenario:
            logger.info(f"正在更新场景: {original_name} -> {new_name}")
            scenario.name = new_name
            scenario.description = description
        # 否则，创建新场景
        else:
            # 再次确认新名称是否已存在（用于全新创建的场景）
            if session.query(Scenario).filter_by(name=new_name).first():
                raise ValueError(f"场景名称 '{new_name}' 已存在。")
            logger.info(f"正在创建新场景: {new_name}")
            new_scenario = Scenario(name=new_name, description=description)
            session.add(new_scenario)
        return True


def delete_scenario_by_name(name: str):
    """通过名称删除场景"""
    with session_scope() as session:
        scenario = session.query(Scenario).filter_by(name=name).first()
        if scenario:
            logger.info(f"正在删除场景: {name}")
            session.delete(scenario)
            return True
        logger.warning(f"尝试删除一个不存在的场景: {name}")
        return False
