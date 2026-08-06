"""LLM 适配器 - 读 settings.json 配置，提供 chat() 方法"""
import json
import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'settings.json')


def _load_settings() -> dict:
    """读取 LLM 配置，不存在则返回空 dict"""
    if not os.path.isfile(SETTINGS_PATH):
        return {}
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('llm', {})
    except Exception as e:
        logger.warning(f"读取 settings.json 失败: {e}")
        return {}


def save_llm_settings(api_key: str = '', base_url: str = '', model: str = '', model_name: str = '') -> dict:
    """保存 LLM 配置到 settings.json（合并写入）"""
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    # 读现有配置
    full = {}
    if os.path.isfile(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                full = json.load(f)
        except Exception:
            full = {}
    llm = full.get('llm', {})
    if api_key:
        llm['api_key'] = api_key
    if base_url:
        llm['base_url'] = base_url
    if model:
        llm['model'] = model
    if model_name:
        llm['model_name'] = model_name
    full['llm'] = llm
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(full, f, ensure_ascii=False, indent=2)
    return llm


def get_llm_settings_masked() -> dict:
    """返回 LLM 配置，api_key 脱敏"""
    llm = _load_settings()
    key = llm.get('api_key', '')
    if key and len(key) > 6:
        masked = key[:3] + '***' + key[-3:]
    elif key:
        masked = '***'
    else:
        masked = ''
    return {
        'api_key': masked,
        'base_url': llm.get('base_url', ''),
        'model': llm.get('model', ''),
        'model_name': llm.get('model_name', ''),
        'configured': bool(llm.get('api_key')),
    }


class LLMAdapter:
    """LLM 调用适配器，基于 OpenAI 兼容协议"""

    def __init__(self):
        self._settings = _load_settings()

    @property
    def is_configured(self) -> bool:
        """是否有有效配置"""
        return bool(self._settings.get('api_key'))

    def chat(self, messages: list[dict]) -> str:
        """
        调用 LLM chat 接口
        :param messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        :return: 助手回复文本
        :raises: RuntimeError 如果未配置或调用失败
        """
        api_key = self._settings.get('api_key', '')
        if not api_key:
            raise RuntimeError('LLM 未配置：请在系统设置中填写 API Key')

        base_url = self._settings.get('base_url', 'https://api.deepseek.com')
        model = self._settings.get('model', 'deepseek-chat')

        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise RuntimeError(f'LLM 调用失败：{e}')
