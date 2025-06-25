import logging
from contextlib import contextmanager
import json
import os
from datetime import datetime
from src.database.database_manager import DatabaseManager
from src.models.data_models import Scenario, Character

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


def get_scenarios_by_character(character_id: int):
    """根据角色ID获取场景，返回字典列表"""
    if not character_id:
        return []
    with session_scope() as session:
        scenarios = (
            session.query(Scenario)
            .filter_by(character_id=character_id)
            .order_by(Scenario.name)
            .all()
        )
        logger.info(f"成功获取角色ID {character_id} 的 {len(scenarios)} 个场景")
        return [
            {"id": s.id, "name": s.name, "description": s.description}
            for s in scenarios
        ]


def get_scenarios_for_display_by_character(character_id: int):
    """根据角色ID获取场景，用于在Dataframe中显示"""
    if not character_id:
        return []
    with session_scope() as session:
        scenarios = (
            session.query(Scenario.name, Scenario.description)
            .filter_by(character_id=character_id)
            .order_by(Scenario.name)
            .all()
        )
        logger.info(f"成功获取角色ID {character_id} 的 {len(scenarios)} 个场景")
        return scenarios if scenarios else []


def save_scenario(
    character_id: int,
    original_name: str = None,
    new_name: str = None,
    description: str = None,
):
    """在指定角色下创建或更新场景。"""
    if not new_name:
        raise ValueError("场景名称不能为空")
    if not character_id:
        raise ValueError("必须提供角色ID")

    with session_scope() as session:
        # 检查新名称是否与该角色的其它场景冲突
        if original_name != new_name:
            existing_with_new_name = (
                session.query(Scenario)
                .filter_by(character_id=character_id, name=new_name)
                .first()
            )
            if existing_with_new_name:
                raise ValueError(f"场景名称 '{new_name}' 在该角色下已存在。")

        scenario = None
        if original_name:
            scenario = (
                session.query(Scenario)
                .filter_by(character_id=character_id, name=original_name)
                .first()
            )

        if scenario:  # 更新
            logger.info(
                f"正在为角色ID {character_id} 更新场景: {original_name} -> {new_name}"
            )
            scenario.name = new_name
            scenario.description = description
        else:  # 创建
            logger.info(f"正在为角色ID {character_id} 创建新场景: {new_name}")
            new_scenario = Scenario(
                name=new_name, description=description, character_id=character_id
            )
            session.add(new_scenario)
        return True


def delete_scenario_by_name(character_id: int, name: str):
    """通过名称删除指定角色的场景"""
    if not character_id:
        raise ValueError("必须提供角色ID")
    with session_scope() as session:
        scenario = (
            session.query(Scenario)
            .filter_by(character_id=character_id, name=name)
            .first()
        )
        if scenario:
            logger.info(f"正在为角色ID {character_id} 删除场景: {name}")
            session.delete(scenario)
            return True
        logger.warning(f"尝试为角色ID {character_id} 删除一个不存在的场景: {name}")
        return False


def export_scenarios_to_json(character_id: int):
    """将指定角色的所有场景导出为JSON文件。"""
    scenarios = get_scenarios_by_character(character_id)
    if not scenarios:
        raise ValueError("该角色下没有任何场景可供导出。")

    export_dir = "export"
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(
        export_dir, f"scenarios_export_{character_id}_{timestamp}.json"
    )

    export_data = [
        {"name": s["name"], "description": s["description"]} for s in scenarios
    ]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=4)

    logger.info(
        f"成功将角色 {character_id} 的 {len(scenarios)} 个场景导出到 {file_path}"
    )
    return file_path


def import_scenarios_from_json(character_id: int, file_path: str):
    """从JSON文件为指定角色导入场景。"""
    if not character_id:
        raise ValueError("必须提供角色ID才能导入场景。")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"读取或解析JSON文件失败: {file_path}, error: {e}")
        raise ValueError("文件格式无效或读取失败。")

    added_count = 0
    skipped_count = 0
    with session_scope() as session:
        for item in data:
            name = item.get("name")
            description = item.get("description")
            if not name:
                logger.warning("导入时发现一个没有名称的场景，已跳过。")
                skipped_count += 1
                continue

            exists = (
                session.query(Scenario)
                .filter_by(character_id=character_id, name=name)
                .first()
            )
            if exists:
                skipped_count += 1
                logger.info(f"角色 {character_id} 的场景 '{name}' 已存在，跳过导入。")
            else:
                new_scenario = Scenario(
                    name=name, description=description, character_id=character_id
                )
                session.add(new_scenario)
                added_count += 1
                logger.info(f"成功为角色 {character_id} 导入新场景: {name}")
    return added_count, skipped_count
