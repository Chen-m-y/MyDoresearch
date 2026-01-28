#!/usr/bin/env python3
"""
DeepSeek论文摘要翻译器 - 最小化实现
"""

import requests
import json
import os
from typing import Optional
from config import DEEPSEEK_API_KEY


class DeepSeekTranslator:
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化翻译器

        Args:
            api_key: DeepSeek API密钥，如果不提供则从环境变量DEEPSEEK_API_KEY读取
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("请提供API密钥或设置环境变量DEEPSEEK_API_KEY")

        self.base_url = "https://api.deepseek.com"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def translate(self, english_text: str) -> str:
        """
        将英文学术摘要翻译为中文

        Args:
            english_text: 英文文本

        Returns:
            中文翻译结果

        Raises:
            Exception: 翻译失败时抛出异常
        """
        system_prompt = """你是专业的学术论文翻译专家。请将以下英文学术摘要翻译成中文，要求：
1. 保持学术严谨性和专业术语准确性
2. 确保翻译流畅自然，符合中文学术表达习惯
3. 保留原文逻辑结构和关键信息
4. 保持数字、百分比等数据原样"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": english_text}
            ],
            "temperature": 0.3,
            "max_tokens": 2048
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            return result['choices'][0]['message']['content'].strip()

        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {e}")
        except KeyError as e:
            raise Exception(f"API响应格式错误: {e}")
        except Exception as e:
            raise Exception(f"翻译失败: {e}")


# 使用示例
if __name__ == "__main__":
    # 设置API密钥（二选一）
    # 方法1: 直接传入
    # translator = DeepSeekTranslator("your_api_key_here")

    # 方法2: 使用环境变量
    # export DEEPSEEK_API_KEY=your_api_key_here
    translator = DeepSeekTranslator(DEEPSEEK_API_KEY)

    # 示例英文摘要
    english_abstract = """An effective traffic management system is crucial to smart city growth. Consequently, the significance of IoT devices is increasing. Numerous IoT devices, including cameras, are commonly positioned along major roads in a smart city. These IoT devices, embedded with computing and transmitting capabilities, collect data from cameras and then relay it to the central traffic controller (CTC) responsible for managing traffic flow. In our study, we introduce a novel framework termed semantic communication (SemCom), which integrates a Convolutional Neural Network (CNN) with a Long Short-Term Memory (LSTM) network."""

    try:
        chinese_translation = translator.translate(english_abstract)

        print("原文:")
        print(english_abstract)
        print("\n译文:")
        print(chinese_translation)

    except Exception as e:
        print(f"翻译出错: {e}")