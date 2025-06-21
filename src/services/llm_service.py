import logging
from string import Template
from src.services import dataset_service, character_service

logger = logging.getLogger(__name__)


def read_prompt_template(
    file_path="templates/prompts/generation_prompt.txt",
) -> Template:
    """Reads the prompt template file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return Template(f.read())
    except FileNotFoundError:
        logger.error(f"提示词模板文件未找到: {file_path}")
        raise


def generate_preview_prompt(
    dataset_name: str, conversation_turns: int, num_to_generate: int
) -> str:
    """
    Generates the final prompt for LLM based on a dataset and parameters.
    """
    if not dataset_name:
        raise ValueError("必须选择一个数据集。")

    # 1. Get dataset details, which includes linked character and scenarios
    dataset = dataset_service.get_dataset_details(dataset_name)
    if not dataset:
        raise ValueError(f"未找到数据集: {dataset_name}")

    character_name = dataset.get("character_name")
    if not character_name:
        raise ValueError(f"数据集 '{dataset_name}' 未绑定任何角色。")

    # 2. Get full character details
    character = character_service.get_character_by_name(character_name)
    if not character:
        raise ValueError(f"未找到角色详情: {character_name}")

    # 3. Get scenario details and format them into a list string
    scenarios = dataset.get("scenario_objects", [])
    scenarios_list_str = "\n".join(
        f"- {s['name']}: {s['description'].replace('{{char}}', character_name)}"
        for s in scenarios
    )
    if not scenarios_list_str:
        scenarios_list_str = "General conversation without specific scenarios."

    # 4. Read the template
    template = read_prompt_template()

    # 5. Substitute the template with data
    prompt_data = {
        "character_name": character.get("name", ""),
        "character_personality": character.get("personality", ""),
        "character_background": character.get("background", ""),
        "character_speaking_style": character.get("speaking_style", ""),
        "conversation_turns": conversation_turns,
        "scenarios_list": scenarios_list_str,
        "dialogue_examples": character.get("dialogue_examples", "N/A"),
        "num_to_generate": num_to_generate,
    }

    final_prompt = template.substitute(prompt_data)
    return final_prompt
