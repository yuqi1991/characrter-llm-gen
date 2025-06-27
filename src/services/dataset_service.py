"""
Service layer for handling dataset-related business logic.
"""

from src.database.database_manager import DatabaseManager
from src.models.data_models import Dataset, Character, Scenario, Corpus
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import logging
import json
import os
import shutil
from datetime import datetime


db_manager = DatabaseManager()
logger = logging.getLogger(__name__)

EXPORT_DIR = "export"


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
        num_to_generate = (
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

        return {
            "total_corpus_count": num_to_generate,
            "scenario_counts": scenario_counts,
        }
    finally:
        session.close()


def delete_corpus_by_scenarios(dataset_id: int, scenario_names: list[str]) -> int:
    """
    Deletes corpus entries from a dataset that are associated with specific scenarios.

    Args:
        dataset_id: The ID of the dataset.
        scenario_names: A list of scenario names to delete corpus for.

    Returns:
        The number of deleted corpus entries.
    """
    if not dataset_id or not scenario_names:
        return 0

    session = db_manager.get_session()
    try:
        # Find scenarios to get their IDs
        scenarios = (
            session.query(Scenario).filter(Scenario.name.in_(scenario_names)).all()
        )
        if not scenarios:
            return 0

        # Find all corpus entries linked to these scenarios within the dataset
        corpus_to_delete = (
            session.query(Corpus)
            .filter(Corpus.dataset_id == dataset_id)
            .join(Corpus.scenarios)
            .filter(Scenario.name.in_(scenario_names))
            .all()
        )

        deleted_count = len(corpus_to_delete)
        if deleted_count > 0:
            for corpus_entry in corpus_to_delete:
                session.delete(corpus_entry)
            session.commit()
            logger.info(
                f"Deleted {deleted_count} corpus entries from dataset {dataset_id} "
                f"for scenarios: {scenario_names}"
            )
        return deleted_count
    except Exception as e:
        session.rollback()
        logger.error(
            f"Error deleting corpus for dataset {dataset_id} "
            f"and scenarios {scenario_names}: {e}",
            exc_info=True,
        )
        raise
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
                    "turn_count": len(conversation.get("dialogues", [])) // 2,
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


def _prepare_export_dir():
    """Prepares the export directory by cleaning and recreating it."""
    try:
        if os.path.exists(EXPORT_DIR):
            for file in os.listdir(EXPORT_DIR):
                file_path = os.path.join(EXPORT_DIR, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(f"删除文件 {file_path} 失败: {e}")
        else:
            os.makedirs(EXPORT_DIR, exist_ok=True)
        logger.info(f"Export directory '{EXPORT_DIR}' prepared.")
    except Exception as e:
        logger.error(f"Failed to prepare export directory: {e}")
        raise


def export_dataset_corpus_to_jsonl(dataset_id: int) -> str:
    """
    导出数据集的所有语料为JSONL格式文件

    Args:
        dataset_id: 数据集ID

    Returns:
        生成的JSONL文件路径
    """
    if not dataset_id:
        raise ValueError("数据集ID不能为空")

    session = db_manager.get_session()
    try:
        # 获取数据集信息
        dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"未找到ID为 {dataset_id} 的数据集")

        # 获取所有语料
        corpus_entries = (
            session.query(Corpus)
            .filter(Corpus.dataset_id == dataset_id)
            .options(joinedload(Corpus.scenarios))
            .order_by(Corpus.created_at.asc())
            .all()
        )

        if not corpus_entries:
            raise ValueError("该数据集没有语料数据")

        _prepare_export_dir()

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"corpus_{dataset.name}_{timestamp}.jsonl"
        filepath = os.path.join(EXPORT_DIR, filename)

        # 生成JSONL内容
        with open(filepath, "w", encoding="utf-8") as f:
            for entry in corpus_entries:
                # 构建标准的对话格式
                jsonl_entry = {
                    "id": entry.id,
                    "dataset_name": dataset.name,
                    "created_at": (
                        entry.created_at.isoformat() if entry.created_at else None
                    ),
                    "scenarios": [s.name for s in entry.scenarios],
                }

                # 处理对话数据
                dialogue_data = entry.dialogue
                if isinstance(dialogue_data, dict):
                    # 如果是结构化数据，直接使用
                    jsonl_entry.update(
                        {
                            "conversations": dialogue_data.get("dialogues", []),
                            "turn_count": dialogue_data.get("turn_count", 0),
                            "batch_id": dialogue_data.get("batch_id", ""),
                            "scenario_labels": dialogue_data.get("scenario_labels", []),
                        }
                    )
                else:
                    # 如果是其他格式，尝试解析
                    try:
                        parsed_dialogue = json.loads(str(dialogue_data))
                        jsonl_entry["conversations"] = parsed_dialogue.get(
                            "dialogues", []
                        )
                        jsonl_entry["turn_count"] = (
                            len(parsed_dialogue.get("dialogues", [])) // 2
                        )
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # 如果解析失败，将原始数据存储为字符串
                        jsonl_entry["raw_dialogue"] = str(dialogue_data)
                        jsonl_entry["conversations"] = []
                        jsonl_entry["turn_count"] = 0

                # 写入JSONL文件（每行一个JSON对象）
                f.write(json.dumps(jsonl_entry, ensure_ascii=False) + "\n")

        logger.info(f"成功导出 {len(corpus_entries)} 条语料到文件: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"导出语料库失败: {e}")
        raise e
    finally:
        session.close()


def export_dataset_corpus_to_standard_format(dataset_id: int) -> str:
    """
    导出数据集的语料为标准训练格式的JSONL文件
    每行包含 {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

    Args:
        dataset_id: 数据集ID

    Returns:
        生成的JSONL文件路径
    """
    if not dataset_id:
        raise ValueError("数据集ID不能为空")

    session = db_manager.get_session()
    try:
        # 获取数据集信息
        dataset = (
            session.query(Dataset)
            .options(joinedload(Dataset.character))
            .filter(Dataset.id == dataset_id)
            .first()
        )
        if not dataset:
            raise ValueError(f"未找到ID为 {dataset_id} 的数据集")

        # 获取所有语料
        corpus_entries = (
            session.query(Corpus)
            .filter(Corpus.dataset_id == dataset_id)
            .options(joinedload(Corpus.scenarios))
            .order_by(Corpus.created_at.asc())
            .all()
        )

        if not corpus_entries:
            raise ValueError("该数据集没有语料数据")

        _prepare_export_dir()

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_{dataset.name}_{timestamp}.jsonl"
        filepath = os.path.join(EXPORT_DIR, filename)

        # 生成标准训练格式的JSONL内容
        with open(filepath, "w", encoding="utf-8") as f:
            for entry in corpus_entries:
                dialogue_data = entry.dialogue

                # 提取对话内容
                messages = []
                if isinstance(dialogue_data, dict) and "dialogues" in dialogue_data:
                    for turn in dialogue_data["dialogues"]:
                        role = turn.get("role", "user")
                        content = turn.get("content", "")
                        if content.strip():  # 只添加非空内容
                            messages.append({"role": role, "content": content})

                # 只有当有有效对话时才写入文件
                if messages and len(messages) >= 2:  # 至少要有一轮完整对话
                    training_entry = {
                        "messages": messages,
                        "metadata": {
                            "dataset": dataset.name,
                            "character": (
                                dataset.character.name if dataset.character else None
                            ),
                            "scenarios": [s.name for s in entry.scenarios],
                            "corpus_id": entry.id,
                        },
                    }
                    f.write(json.dumps(training_entry, ensure_ascii=False) + "\n")

        logger.info(f"成功导出标准训练格式文件: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"导出标准训练格式失败: {e}")
        raise e
    finally:
        session.close()


# TODO: Implement dataset service functions here.
# - get_dataset_stats(dataset_id)


def detect_invalid_corpus_data(dataset_id: int = None) -> dict:
    """
    检测数据集中不合规范的语料数据

    Args:
        dataset_id: 数据集ID，如果为None则检测所有数据集

    Returns:
        包含检测结果的字典，格式为：
        {
            "total_checked": int,
            "invalid_entries": [
                {
                    "corpus_id": int,
                    "dataset_name": str,
                    "issues": [str],  # 问题描述列表
                    "dialogue_sample": str  # 问题数据样本
                }
            ]
        }
    """
    session = db_manager.get_session()
    try:
        # 构建查询
        query = session.query(Corpus).options(joinedload(Corpus.dataset))
        if dataset_id:
            query = query.filter(Corpus.dataset_id == dataset_id)

        corpus_entries = query.all()

        invalid_entries = []
        total_checked = len(corpus_entries)

        for entry in corpus_entries:
            issues = []
            dialogue_sample = ""

            try:
                dialogue_data = entry.dialogue

                # 检查dialogue_data是否为字典
                if not isinstance(dialogue_data, dict):
                    issues.append("dialogue字段不是字典类型")
                    dialogue_sample = str(dialogue_data)[:100] + "..."
                    invalid_entries.append(
                        {
                            "corpus_id": entry.id,
                            "dataset_name": (
                                entry.dataset.name if entry.dataset else "未知"
                            ),
                            "issues": issues,
                            "dialogue_sample": dialogue_sample,
                        }
                    )
                    continue

                # 检查是否包含dialogues字段
                if "dialogues" not in dialogue_data:
                    issues.append("缺少dialogues字段")
                else:
                    dialogues = dialogue_data["dialogues"]

                    # 检查dialogues是否为列表
                    if not isinstance(dialogues, list):
                        issues.append("dialogues字段不是列表类型")
                    else:
                        # 检查每个对话回合
                        for i, turn in enumerate(dialogues):
                            if not isinstance(turn, dict):
                                issues.append(f"第{i+1}轮对话不是字典类型")
                                continue

                            # 检查role字段
                            role = turn.get("role")
                            if not role or not isinstance(role, str):
                                issues.append(f"第{i+1}轮对话缺少有效的role字段")

                            # 检查content字段
                            content = turn.get("content")
                            if content is None:
                                issues.append(f"第{i+1}轮对话缺少content字段")
                            elif isinstance(content, dict):
                                issues.append(
                                    f"第{i+1}轮对话的content是字典类型而非字符串"
                                )
                            elif not isinstance(content, str):
                                issues.append(
                                    f"第{i+1}轮对话的content不是字符串类型：{type(content)}"
                                )

                # 如果发现问题，记录这个条目
                if issues:
                    # 生成问题数据样本
                    if isinstance(dialogue_data, dict) and "dialogues" in dialogue_data:
                        sample_turns = dialogue_data["dialogues"][:2]  # 只取前两轮
                        dialogue_sample = (
                            json.dumps(sample_turns, ensure_ascii=False)[:200] + "..."
                        )
                    else:
                        dialogue_sample = str(dialogue_data)[:100] + "..."

                    invalid_entries.append(
                        {
                            "corpus_id": entry.id,
                            "dataset_name": (
                                entry.dataset.name if entry.dataset else "未知"
                            ),
                            "issues": issues,
                            "dialogue_sample": dialogue_sample,
                        }
                    )

            except Exception as e:
                issues.append(f"数据解析异常: {str(e)}")
                invalid_entries.append(
                    {
                        "corpus_id": entry.id,
                        "dataset_name": entry.dataset.name if entry.dataset else "未知",
                        "issues": issues,
                        "dialogue_sample": str(entry.dialogue)[:100] + "...",
                    }
                )

        logger.info(
            f"检测完成：总共检查 {total_checked} 条语料，发现 {len(invalid_entries)} 条不合规范数据"
        )

        return {"total_checked": total_checked, "invalid_entries": invalid_entries}

    finally:
        session.close()


def clean_invalid_corpus_data(dataset_id: int = None, dry_run: bool = True) -> dict:
    """
    清理数据集中不合规范的语料数据

    Args:
        dataset_id: 数据集ID，如果为None则清理所有数据集
        dry_run: 是否为试运行模式，True时只检测不删除

    Returns:
        包含清理结果的字典，格式为：
        {
            "detected_count": int,
            "deleted_count": int,
            "dry_run": bool,
            "deleted_corpus_ids": [int]
        }
    """
    # 首先检测不合规范的数据
    detection_result = detect_invalid_corpus_data(dataset_id)
    invalid_entries = detection_result["invalid_entries"]

    if not invalid_entries:
        logger.info("未发现不合规范的语料数据")
        return {
            "detected_count": 0,
            "deleted_count": 0,
            "dry_run": dry_run,
            "deleted_corpus_ids": [],
        }

    if dry_run:
        logger.info(
            f"试运行模式：发现 {len(invalid_entries)} 条不合规范数据，但不会删除"
        )
        return {
            "detected_count": len(invalid_entries),
            "deleted_count": 0,
            "dry_run": True,
            "deleted_corpus_ids": [],
        }

    # 执行删除操作
    session = db_manager.get_session()
    deleted_corpus_ids = []
    deleted_count = 0

    try:
        corpus_ids_to_delete = [entry["corpus_id"] for entry in invalid_entries]

        # 批量删除
        for corpus_id in corpus_ids_to_delete:
            try:
                corpus_entry = (
                    session.query(Corpus).filter(Corpus.id == corpus_id).first()
                )
                if corpus_entry:
                    session.delete(corpus_entry)
                    deleted_corpus_ids.append(corpus_id)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"删除语料ID {corpus_id} 时出错: {e}")
                continue

        session.commit()
        logger.info(f"成功删除 {deleted_count} 条不合规范的语料数据")

        return {
            "detected_count": len(invalid_entries),
            "deleted_count": deleted_count,
            "dry_run": False,
            "deleted_corpus_ids": deleted_corpus_ids,
        }

    except Exception as e:
        session.rollback()
        logger.error(f"批量删除语料数据时出错: {e}")
        raise e
    finally:
        session.close()
