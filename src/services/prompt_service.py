import os
from typing import List

PROMPT_DIR = "templates/prompts"


def get_prompt_files() -> List[str]:
    """
    返回 prompts 目录中所有 .txt 文件的列表。
    """
    if not os.path.exists(PROMPT_DIR):
        os.makedirs(PROMPT_DIR)
        return []

    files = [f for f in os.listdir(PROMPT_DIR) if f.endswith(".txt")]
    return sorted(files)


def read_prompt_file(filename: str) -> str:
    """
    读取提示词文件的内容。
    """
    if not filename:
        return ""
    if not filename.endswith(".txt"):
        filename += ".txt"

    filepath = os.path.join(PROMPT_DIR, filename)
    if not os.path.exists(filepath):
        return ""

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def save_prompt_file(filename: str, content: str) -> str:
    """
    将内容保存到提示词文件。如果文件不存在，则创建它。
    返回成功消息。
    """
    if not filename:
        return "❌ 错误：文件名不能为空"

    if not filename.endswith(".txt"):
        filename += ".txt"

    # 防止目录遍历
    if "/" in filename or "\\" in filename:
        return "❌ 错误：文件名无效"

    filepath = os.path.join(PROMPT_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 提示词 '{filename}' 保存成功！"
    except Exception as e:
        return f"❌ 保存失败: {e}"


def delete_prompt_file(filename: str) -> str:
    """
    删除提示词文件。
    返回成功消息。
    """
    if not filename:
        return "❌ 错误：文件名不能为空"

    if not filename.endswith(".txt"):
        filename += ".txt"

    # 防止目录遍历
    if "/" in filename or "\\" in filename:
        return "❌ 错误：文件名无效"

    filepath = os.path.join(PROMPT_DIR, filename)

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return f"✅ 提示词 '{filename}' 删除成功！"
        except Exception as e:
            return f"❌ 删除失败: {e}"
    else:
        return f"⚠️ 提示词 '{filename}' 不存在。"
