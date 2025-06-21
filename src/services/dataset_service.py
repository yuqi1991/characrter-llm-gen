"""
Service layer for handling dataset-related business logic.
"""

from src.database.database_manager import DatabaseManager
from src.models.data_models import Dataset, Character, Scenario, Corpus
from sqlalchemy.orm import joinedload
from sqlalchemy import func


db_manager = DatabaseManager()


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


# TODO: Implement dataset service functions here.
# - get_dataset_stats(dataset_id)
