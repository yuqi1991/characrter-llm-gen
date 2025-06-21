"""
Service layer for handling dataset-related business logic.
"""

from src.database.database_manager import DatabaseManager
from src.models.data_models import Dataset, Character, Scenario, Corpus
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import logging


db_manager = DatabaseManager()
logger = logging.getLogger(__name__)


def get_all_datasets_for_display():
    """Fetches all datasets for display in a dropdown."""
    session = db_manager.get_session()
    try:
        datasets = session.query(Dataset).order_by(Dataset.name).all()
        return [{"id": d.id, "name": d.name} for d in datasets]
    finally:
        session.close()


def create_or_update_dataset(
    dataset_id, name, description, character_name, scenario_names
):
    """
    Creates a new dataset or updates an existing one.
    - dataset_id: The ID of the dataset to update, or None to create a new one.
    - name: The name of the dataset.
    - description: The description of the dataset.
    - character_name: The name of the character to associate.
    - scenario_names: A list of names of the scenarios to associate.
    """
    session = db_manager.get_session()
    try:
        # Check for duplicate name
        existing_dataset = session.query(Dataset).filter(Dataset.name == name).first()
        if existing_dataset and existing_dataset.id != dataset_id:
            raise ValueError(f"数据集名称 '{name}' 已存在，请使用其他名称。")

        # Get character object
        character = (
            session.query(Character).filter(Character.name == character_name).first()
        )
        if not character:
            raise ValueError(f"未找到角色 '{character_name}'。")

        # Get scenario objects
        scenarios = (
            session.query(Scenario).filter(Scenario.name.in_(scenario_names)).all()
        )

        if dataset_id:
            # Update existing dataset
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).one()
            dataset.name = name
            dataset.description = description
            dataset.character = character
            dataset.scenarios = scenarios
        else:
            # Create new dataset
            dataset = Dataset(
                name=name,
                description=description,
                character=character,
                scenarios=scenarios,
            )
            session.add(dataset)

        session.commit()

        # Return the ID of the created/updated dataset
        return dataset.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_dataset_details(dataset_name):
    """Fetches the details of a single dataset by its name."""
    session = db_manager.get_session()
    try:
        dataset = (
            session.query(Dataset)
            .options(joinedload(Dataset.character), joinedload(Dataset.scenarios))
            .filter(Dataset.name == dataset_name)
            .first()
        )

        if not dataset:
            return None

        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "character_name": dataset.character.name if dataset.character else None,
            "scenario_names": [s.name for s in dataset.scenarios],
            "scenario_objects": [
                {"name": s.name, "description": s.description}
                for s in dataset.scenarios
            ],
        }
    finally:
        session.close()


def get_dataset_details_by_id(dataset_id):
    """Fetches the details of a single dataset by its ID."""
    if not dataset_id:
        return None
    session = db_manager.get_session()
    try:
        dataset = (
            session.query(Dataset)
            .options(joinedload(Dataset.character), joinedload(Dataset.scenarios))
            .filter(Dataset.id == dataset_id)
            .first()
        )

        if not dataset:
            return None

        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "character_name": dataset.character.name if dataset.character else None,
            "scenario_names": [s.name for s in dataset.scenarios],
            "scenario_objects": [
                {"name": s.name, "description": s.description}
                for s in dataset.scenarios
            ],
        }
    finally:
        session.close()


def delete_dataset(dataset_id):
    """Deletes a dataset and its associated corpus entries."""
    if not dataset_id:
        return False

    session = db_manager.get_session()
    try:
        dataset = session.query(Dataset).filter(Dataset.id == dataset_id).one()
        session.delete(dataset)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        # Log the exception for debugging
        print(f"Error deleting dataset: {e}")
        return False
    finally:
        session.close()


def get_corpus_by_dataset(dataset_id, scenario_filter_names=None):
    """
    Fetches corpus entries for a given dataset, optionally filtered by scenarios.
    Returns a list of dictionaries, each representing a corpus entry.
    """
    if not dataset_id:
        return []

    session = db_manager.get_session()
    try:
        query = (
            session.query(Corpus)
            .filter(Corpus.dataset_id == dataset_id)
            .options(joinedload(Corpus.scenarios))
        )

        if scenario_filter_names:
            query = query.join(Corpus.scenarios).filter(
                Scenario.name.in_(scenario_filter_names)
            )

        corpus_entries = query.order_by(Corpus.created_at.desc()).all()

        result = []
        for entry in corpus_entries:
            result.append(
                {
                    "dialogue": entry.dialogue,
                    "scenarios": ", ".join([s.name for s in entry.scenarios]),
                }
            )
        return result
    finally:
        session.close()


def get_dataset_stats(dataset_id):
    """
    Calculates statistics for a given dataset.
    - Total number of corpus entries.
    - Count of corpus entries per scenario.
    """
    if not dataset_id:
        return {"total_corpus_count": 0, "scenario_counts": {}}

    session = db_manager.get_session()
    try:
        # Get total count
        total_count = (
            session.query(Corpus).filter(Corpus.dataset_id == dataset_id).count()
        )

        # Get count per scenario
        # This requires a join and group by
        scenario_counts_query = (
            session.query(Scenario.name, func.count(Corpus.id))
            .join(Corpus.scenarios)
            .filter(Corpus.dataset_id == dataset_id)
            .group_by(Scenario.name)
            .all()
        )

        scenario_counts = {name: count for name, count in scenario_counts_query}

        return {"total_corpus_count": total_count, "scenario_counts": scenario_counts}
    finally:
        session.close()


def save_corpus_to_dataset(
    dataset_name: str, dialogue_data: dict, scenario_names: list
) -> int:
    """
    保存一条语料到指定数据集

    Args:
        dataset_name: 目标数据集名称
        dialogue_data: 对话数据，包含dialogues、scenario_labels等字段
        scenario_names: 关联的场景标签名称列表

    Returns:
        保存的语料ID
    """
    session = db_manager.get_session()
    try:
        # 获取数据集
        dataset = session.query(Dataset).filter(Dataset.name == dataset_name).first()
        if not dataset:
            raise ValueError(f"数据集 '{dataset_name}' 不存在")

        # 获取场景对象
        scenarios = []
        if scenario_names:
            scenarios = (
                session.query(Scenario).filter(Scenario.name.in_(scenario_names)).all()
            )

        # 创建语料条目
        corpus = Corpus(dialogue=dialogue_data, dataset=dataset, scenarios=scenarios)

        session.add(corpus)
        session.commit()

        logger.info(f"成功保存语料到数据集 '{dataset_name}'，ID: {corpus.id}")
        return corpus.id

    except Exception as e:
        session.rollback()
        logger.error(f"保存语料失败: {e}")
        raise e
    finally:
        session.close()


def batch_save_corpus_to_dataset(dataset_name: str, conversations: list) -> int:
    """
    批量保存语料到指定数据集

    Args:
        dataset_name: 目标数据集名称
        conversations: 对话列表，每个元素包含对话数据和场景信息

    Returns:
        成功保存的语料数量
    """
    session = db_manager.get_session()
    saved_count = 0

    try:
        # 获取数据集
        dataset = session.query(Dataset).filter(Dataset.name == dataset_name).first()
        if not dataset:
            raise ValueError(f"数据集 '{dataset_name}' 不存在")

        # 获取所有可能的场景
        all_scenario_names = set()
        for conv in conversations:
            all_scenario_names.update(conv.get("scenarios", []))

        scenarios_dict = {}
        if all_scenario_names:
            scenarios = (
                session.query(Scenario)
                .filter(Scenario.name.in_(all_scenario_names))
                .all()
            )
            scenarios_dict = {s.name: s for s in scenarios}

        # 批量创建语料条目
        for conversation in conversations:
            try:
                # 转换对话格式
                dialogue_data = {
                    "scenario_labels": conversation.get("scenarios", []),
                    "dialogues": conversation.get("dialogues", []),
                    "turn_count": len(conversation.get("dialogues", [])),
                    "batch_id": conversation.get("batch_id"),
                    "generation_time": conversation.get("generation_time"),
                }

                # 获取相关场景
                conv_scenarios = []
                for scenario_name in conversation.get("scenarios", []):
                    if scenario_name in scenarios_dict:
                        conv_scenarios.append(scenarios_dict[scenario_name])

                # 创建语料条目
                corpus = Corpus(
                    dialogue=dialogue_data, dataset=dataset, scenarios=conv_scenarios
                )

                session.add(corpus)
                saved_count += 1

            except Exception as e:
                logger.error(f"保存单条语料失败: {e}")
                continue

        session.commit()
        logger.info(
            f"批量保存完成，成功保存 {saved_count}/{len(conversations)} 条语料到数据集 '{dataset_name}'"
        )
        return saved_count

    except Exception as e:
        session.rollback()
        logger.error(f"批量保存语料失败: {e}")
        raise e
    finally:
        session.close()


def get_corpus_preview_data(dataset_id: int, limit: int = 50) -> list:
    """
    获取数据集的语料预览数据

    Args:
        dataset_id: 数据集ID
        limit: 返回的最大条数

    Returns:
        语料预览数据列表
    """
    if not dataset_id:
        return []

    session = db_manager.get_session()
    try:
        corpus_entries = (
            session.query(Corpus)
            .filter(Corpus.dataset_id == dataset_id)
            .options(joinedload(Corpus.scenarios))
            .order_by(Corpus.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for entry in corpus_entries:
            dialogue_data = entry.dialogue
            scenarios_str = ", ".join([s.name for s in entry.scenarios])

            # 格式化对话内容为可读形式
            if isinstance(dialogue_data, dict) and "dialogues" in dialogue_data:
                dialogue_text = ""
                for turn in dialogue_data["dialogues"]:
                    role = turn.get("role", "unknown")
                    content = turn.get("content", "")
                    dialogue_text += f"{role}: {content}\n"
            else:
                dialogue_text = str(dialogue_data)

            result.append(
                {
                    "id": entry.id,
                    "scenarios": scenarios_str,
                    "dialogue_text": dialogue_text.strip(),
                    "turn_count": (
                        dialogue_data.get("turn_count", 0)
                        if isinstance(dialogue_data, dict)
                        else 0
                    ),
                    "created_at": (
                        entry.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if entry.created_at
                        else ""
                    ),
                    "batch_id": (
                        dialogue_data.get("batch_id", "")
                        if isinstance(dialogue_data, dict)
                        else ""
                    ),
                }
            )

        return result

    finally:
        session.close()


# TODO: Implement dataset service functions here.
# - get_dataset_stats(dataset_id)
