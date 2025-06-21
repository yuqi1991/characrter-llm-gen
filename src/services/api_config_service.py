"""
Service for managing API configurations.
Handles CRUD operations and encryption for API keys.
"""

import logging
from contextlib import contextmanager
from src.database.database_manager import DatabaseManager
from src.models.data_models import ApiConfig
from openai import OpenAI
import google.generativeai as genai


# We will need an encryption utility. For now, we can create placeholder functions.
# In a real application, use a robust library like 'cryptography'.
def encrypt_key(key: str) -> str:
    # Placeholder: In a real scenario, this would be a strong encryption
    return f"encrypted_{key}"


def decrypt_key(encrypted_key: str) -> str:
    # Placeholder: In a real scenario, this would be a strong decryption
    if encrypted_key and encrypted_key.startswith("encrypted_"):
        return encrypted_key[len("encrypted_") :]
    return encrypted_key


logger = logging.getLogger(__name__)
db_manager = DatabaseManager()


def save_api_config(
    name: str,
    api_type: str,
    api_key: str,
    base_url: str = None,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
):
    """Saves or updates an API configuration."""
    if not name or not api_type or not api_key:
        raise ValueError("配置名称、API类型和API Key不能为空。")

    session = db_manager.get_session()
    try:
        # Encrypt sensitive information
        api_key_encrypted = encrypt_key(api_key)
        base_url_encrypted = encrypt_key(base_url) if base_url else None

        # Check if config with this name already exists
        config = session.query(ApiConfig).filter_by(name=name).first()

        if config:
            # Update existing config
            logger.info(f"正在更新API配置: {name}")
            config.api_type = api_type
            config.api_key_encrypted = api_key_encrypted
            config.base_url_encrypted = base_url_encrypted
            config.top_p = top_p
            config.frequency_penalty = frequency_penalty
            config.presence_penalty = presence_penalty
        else:
            # Create new config
            logger.info(f"正在创建新的API配置: {name}")
            config = ApiConfig(
                name=name,
                api_type=api_type,
                api_key_encrypted=api_key_encrypted,
                base_url_encrypted=base_url_encrypted,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            session.add(config)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_all_api_configs():
    """Fetches all saved API configurations for display."""
    session = db_manager.get_session()
    try:
        configs = session.query(ApiConfig).order_by(ApiConfig.name).all()
        # Return a list of dictionaries, decrypting where necessary
        return [
            {
                "name": c.name,
                "api_type": c.api_type,
                "base_url": (
                    decrypt_key(c.base_url_encrypted) if c.base_url_encrypted else ""
                ),
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M"),
                # Also return other params so they can be loaded into the form
                "top_p": c.top_p,
                "frequency_penalty": c.frequency_penalty,
                "presence_penalty": c.presence_penalty,
            }
            for c in configs
        ]
    finally:
        session.close()


def get_api_config_by_name(name: str):
    """Fetches a single API config by name, with the key decrypted."""
    if not name:
        return None
    session = db_manager.get_session()
    try:
        config = session.query(ApiConfig).filter_by(name=name).first()
        if not config:
            return None

        return {
            "name": config.name,
            "api_type": config.api_type,
            "api_key": decrypt_key(config.api_key_encrypted),
            "base_url": (
                decrypt_key(config.base_url_encrypted)
                if config.base_url_encrypted
                else ""
            ),
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
        }
    finally:
        session.close()


def delete_api_config(name: str):
    """Deletes an API configuration by its name."""
    if not name:
        return False
    session = db_manager.get_session()
    try:
        config = session.query(ApiConfig).filter_by(name=name).first()
        if config:
            logger.info(f"正在删除API配置: {name}")
            session.delete(config)
            session.commit()
            return True
        logger.warning(f"尝试删除一个不存在的API配置: {name}")
        return False
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_available_models(api_config_name: str) -> list[str]:
    """Fetches available models from the provider based on the saved config."""
    if not api_config_name:
        return []

    config = get_api_config_by_name(api_config_name)
    if not config:
        raise ValueError("API配置不存在。")

    api_type = config["api_type"]
    api_key = config["api_key"]
    base_url = config.get("base_url")

    try:
        if api_type == "OpenAI":
            logger.info(f"正在从 {base_url}-{api_key} 获取模型列表...")
            client = OpenAI(
                api_key=api_key.strip(), base_url=base_url.strip() if base_url else None
            )
            models = client.models.list()
            model_ids = [model.id for model in models.data]
            # Filter for common chat models and sort them
            return sorted(model_ids)

        elif api_type == "Google":
            # Google AI Python SDK uses a different mechanism, often listing models is simpler
            # For this example, we'll list some known models.
            # A real implementation might require more complex auth.
            genai.configure(api_key=api_key)
            return sorted(
                [
                    m.name
                    for m in genai.list_models()
                    if "generateContent" in m.supported_generation_methods
                ]
            )

        elif api_type == "Anthropic":
            # Anthropic library would be needed here. For now, returning hardcoded list.
            # import anthropic
            return sorted(
                [
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                    "claude-2.1",
                ]
            )

    except Exception as e:
        logger.error(f"无法从 {api_type} 获取模型列表: {e}", exc_info=True)
        # Re-raise as a generic error to be caught by the UI
        raise RuntimeError(f"获取模型列表失败: {str(e)}") from e

    return []


# TODO: Implement API Config service functions here.
# - test_api_connection(config) -> bool, str
