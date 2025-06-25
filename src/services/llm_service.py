import logging
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Optional, Any
from string import Template
from openai import OpenAI, AsyncOpenAI
from google import genai
from pydantic import BaseModel, Field
from src.services import dataset_service, character_service, api_config_service
import os
import glob

logger = logging.getLogger(__name__)


# Pydantic models for structured output
class DialogueTurn(BaseModel):
    """单轮对话结构"""

    role: str = Field(description="发言者角色：'user' 或 'assistant'")
    content: str = Field(description="对话内容")


class ConversationItem(BaseModel):
    """单条对话结构"""

    scenarios: List[str] = Field(description="对话涉及的场景标签列表")
    dialogues: List[DialogueTurn] = Field(description="对话轮次列表")


class GenerationResult(BaseModel):
    """生成结果结构"""

    conversations: List[ConversationItem] = Field(description="生成的对话列表")


class GenerationBatch(BaseModel):
    """生成批次信息"""

    batch_id: str
    dataset_name: str
    character_name: str
    scenario_names: List[str]
    total_requested: int
    completed: int = 0
    failed: int = 0
    results: List[Dict[str, Any]] = []
    start_time: datetime
    end_time: Optional[datetime] = None


def get_prompt_templates() -> List[Dict[str, str]]:
    """获取所有可用的提示词模板文件列表"""
    try:
        template_dir = "templates/prompts"
        if not os.path.exists(template_dir):
            return [
                {"name": "默认模板", "path": "templates/prompts/generation_prompt.txt"}
            ]

        # 获取所有.txt文件
        pattern = os.path.join(template_dir, "*.txt")
        template_files = glob.glob(pattern)

        templates = []
        for file_path in template_files:
            filename = os.path.basename(file_path)
            templates.append({"name": filename, "path": file_path})

        # 按名称排序，确保默认模板在前面
        templates.sort(key=lambda x: (x["name"] != "默认模板", x["name"]))
        return templates
    except Exception as e:
        logger.error(f"获取模板文件列表失败: {e}")
        return [{"name": "默认模板", "path": "templates/prompts/generation_prompt.txt"}]


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
    dataset_name: str,
    conversation_turns: int,
    num_to_generate: int,
    template_path: str = "templates/prompts/generation_prompt.txt",
) -> str:
    """
    Generates the final prompt for LLM based on a dataset and parameters.
    """
    if not dataset_name:
        return "⚠️ 请先选择一个数据集再预览提示词。\n\n📝 使用说明：\n1. 在左侧面板选择一个数据集\n2. 选择合适的提示词模板\n3. 调整对话轮数和生成数量\n4. 点击此按钮预览最终提示词"

    # 1. Get dataset details, which includes linked character and scenarios
    try:
        dataset = dataset_service.get_dataset_details(dataset_name)
        if not dataset:
            return f"❌ 错误：未找到数据集 '{dataset_name}'。请检查数据集是否存在。"

        character_name = dataset.get("character_name")
        if not character_name:
            return f"❌ 错误：数据集 '{dataset_name}' 未绑定任何角色。请先为数据集配置角色。"

        # 2. Get full character details
        character = character_service.get_character_by_name(character_name)
        if not character:
            return f"❌ 错误：未找到角色详情 '{character_name}'。请检查角色是否存在。"

        # 3. Get scenario details and format them into a list string
        scenarios = dataset.get("scenario_objects", [])
        scenarios_list_str = "\n".join(
            f"\n- {i+1}. {s['name']}:\n {s['description'].replace('{{char}}', character_name)}"
            for i, s in enumerate(scenarios)
        )
        if not scenarios_list_str:
            scenarios_list_str = "General conversation without specific scenarios."

        # 4. Read the template with specified path
        template = read_prompt_template(template_path)

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

    except Exception as e:
        logger.error(f"生成预览提示词时发生错误: {e}")
        return f"❌ 生成预览时发生错误：{str(e)}\n\n请检查：\n- 数据集是否正确配置\n- 角色信息是否完整\n- 场景设置是否正确\n- 模板文件是否存在"


async def call_openai_structured(
    client: AsyncOpenAI,
    prompt: str,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 1.0,
    frequency_penalty: float = 0.5,
    presence_penalty: float = 0.5,
    **kwargs,
) -> Dict[str, Any]:
    """调用OpenAI API并要求结构化输出"""
    try:
        logger.debug(prompt)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "请你执行以下用户要求的任务",
                },
                {"role": "user", "content": prompt},
            ],
            # response_format=GenerationResult,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            **kwargs,
        )

        if response.choices[0].message.content:
            logger.debug(response.choices[0].message.content)
            try:
                content = response.choices[0].message.content
                clean_string = content.removeprefix("```json\n").removesuffix("\n```")
                json_content = json.loads(clean_string)  # 直接解析JSON
                if isinstance(json_content, list):
                    return {"conversations": json_content}
                elif isinstance(json_content, dict) and "conversations" in json_content:
                    return json_content
                else:
                    return {"conversations": []}
            except json.JSONDecodeError:
                logger.error(
                    f"无法解析响应为JSON: \n {response.choices[0].message.content}"
                )
                return {"conversations": []}
        else:
            # Fallback to regular content if parsing fails
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                logger.error(f"无法解析响应为JSON: {content}")
                return {"conversations": []}

    except Exception as e:
        logger.error(f"OpenAI API调用失败: {e}")
        raise


async def call_google_structured(
    api_key: str,
    prompt: str,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
) -> Dict[str, Any]:
    """调用Google AI API并解析结构化输出"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model)

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = await model.generate_content_async(
            prompt, generation_config=generation_config
        )

        content = response.text
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"无法解析Google响应为JSON: {content}")
            return {"conversations": []}

    except Exception as e:
        logger.error(f"Google AI API调用失败: {e}")
        raise


async def generate_single_batch(
    api_config: Dict[str, Any],
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    frequency_penalty: float,
    presence_penalty: float,
) -> Dict[str, Any]:
    """生成单个批次的对话"""
    api_type = api_config["api_type"]
    api_key = api_config["api_key"]
    base_url = api_config.get("base_url")

    if api_type == "OpenAI":
        client = AsyncOpenAI(
            api_key=api_key.strip(), base_url=base_url.strip() if base_url else None
        )
        return await call_openai_structured(
            client,
            prompt,
            model,
            temperature,
            max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
    elif api_type == "Google":
        return await call_google_structured(
            api_key, prompt, model, temperature, max_tokens
        )
    else:
        raise ValueError(f"不支持的API类型: {api_type}")


async def generate_corpus_batch(
    dataset_name: str,
    api_config_name: str,
    model_name: str,
    num_to_generate: int,
    conversation_turns: int,
    total_requests: int,
    max_parallel_requests: int,
    batch_cooldown_seconds: int,
    temperature: float = 0.7,
    max_tokens: int = 8096,
    top_p: float = 1.0,
    frequency_penalty: float = 0.5,
    presence_penalty: float = 0.5,
    template_path: str = "templates/prompts/generation_prompt.txt",
    progress_callback=None,
) -> GenerationBatch:
    """异步批量生成语料数据"""

    # 获取API配置
    api_config = api_config_service.get_api_config_by_name(api_config_name)
    if not api_config:
        raise ValueError(f"API配置 '{api_config_name}' 不存在")

    # 获取数据集信息
    dataset = dataset_service.get_dataset_details(dataset_name)
    if not dataset:
        raise ValueError(f"数据集 '{dataset_name}' 不存在")

    # 生成基础提示词
    base_prompt = generate_preview_prompt(
        dataset_name, conversation_turns, num_to_generate, template_path
    )  # 模板中用1，后续会替换

    # 创建批次信息
    batch = GenerationBatch(
        batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        dataset_name=dataset_name,
        character_name=dataset.get("character_name", ""),
        scenario_names=[s["name"] for s in dataset.get("scenario_objects", [])],
        total_requested=total_requests * num_to_generate,
        start_time=datetime.now(),
    )

    # 创建任务列表
    tasks = []
    for i in range(total_requests):
        task = generate_single_batch(
            api_config=api_config,
            prompt=base_prompt,
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        await asyncio.sleep(1)  # 防止请求过于频繁
        tasks.append(task)
        logger.info(f"生成任务 {i+1} 已添加: 请求生成{num_to_generate} 条语料")
        if i % max_parallel_requests == 0:
            await asyncio.sleep(batch_cooldown_seconds)

    logger.info(
        f"开始并行生成 {len(tasks)} 个批次，每次请求生成 {num_to_generate} 条对话，最大并行请求数 {max_parallel_requests}，\
            冷却时间 {batch_cooldown_seconds} 秒，总请求数量 {total_requests}"
    )

    # 并行执行所有任务
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批次 {i+1} 生成失败: {result}")
                batch.failed += 1
                if progress_callback:
                    progress_callback(f"批次 {i+1} 失败: {str(result)}")
            else:
                conversations = result.get("conversations", [])
                batch.results.extend(conversations)
                batch.completed += len(conversations)
                logger.info(f"批次 {i+1} 成功生成 {len(conversations)} 条对话")
                if progress_callback:
                    progress_callback(
                        f"批次 {i+1} 完成，生成 {len(conversations)} 条对话"
                    )

    except Exception as e:
        logger.error(f"批量生成过程中出现错误: {e}")
        batch.failed = len(tasks)
        if progress_callback:
            progress_callback(f"生成失败: {str(e)}")

    batch.end_time = datetime.now()
    total_time = (batch.end_time - batch.start_time).total_seconds()
    logger.info(
        f"批次 {batch.batch_id} 完成: 成功 {batch.completed}/{batch.total_requested}，用时 {total_time:.2f}秒"
    )

    return batch


def save_generation_results(batch: GenerationBatch, dataset_name: str) -> int:
    """将生成结果保存到数据库"""
    from src.services.dataset_service import save_corpus_to_dataset

    saved_count = 0
    for conversation in batch.results:
        try:
            # 转换为所需格式
            dialogue_data = {
                "scenario_labels": conversation.get("scenarios", []),
                "dialogues": [
                    {
                        "role": turn.get("role", "user"),
                        "content": turn.get("content", ""),
                    }
                    for turn in conversation.get("dialogues", [])
                ],
                "turn_count": len(conversation.get("dialogues", [])) // 2,
                "batch_id": batch.batch_id,
                "generation_time": batch.start_time.isoformat(),
            }

            scenario_names = conversation.get("scenarios", [])
            save_corpus_to_dataset(dataset_name, dialogue_data, scenario_names)
            saved_count += 1

        except Exception as e:
            logger.error(f"保存对话失败: {e}")

    logger.info(
        f"成功保存 {saved_count}/{len(batch.results)} 条对话到数据集 '{dataset_name}'"
    )
    return saved_count
