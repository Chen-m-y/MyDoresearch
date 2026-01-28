"""
DeepSeek深度分析服务 - 基于PDF文本解析
先本地解析PDF为文本，再发送给DeepSeek分析
"""
import time
import requests
import base64
import json
from typing import Optional
from config import DEEPSEEK_API_KEY


class DeepSeekAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def analyze_pdf(self, pdf_content: bytes, paper_title: str) -> str:
        """分析PDF内容 - 先解析文本再分析"""
        if not self.api_key or self.api_key == 'your_api_key_here':
            raise Exception("请配置有效的DeepSeek API密钥")

        print(f"🧠 开始分析PDF...")
        print(f"📝 论文标题: {paper_title}")
        print(f"📄 PDF大小: {len(pdf_content) / 1024 / 1024:.2f}MB")

        # 步骤1: 提取PDF文本
        print("📄 正在提取PDF文本...")
        pdf_text = self._extract_pdf_text(pdf_content)

        if not pdf_text or len(pdf_text.strip()) < 100:
            print("⚠️ PDF文本提取失败或内容过少，使用标题进行分析")
            return self._analyze_title_only(paper_title)

        print(f"✅ PDF文本提取成功，长度: {len(pdf_text)}字符")

        # 步骤2: 使用提取的文本进行分析
        return self.analyze_with_pdf_text(pdf_text, paper_title)

    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """提取PDF文本内容"""
        try:
            # 方法2: 尝试使用pdfplumber
            try:
                import pdfplumber
                import io

                print("🔧 使用pdfplumber提取文本...")
                pdf_file = io.BytesIO(pdf_content)
                text = ""

                with pdfplumber.open(pdf_file) as pdf:
                    total_pages = len(pdf.pages)
                    print(f"📄 PDF总页数: {total_pages}")

                    max_chars = 50000  # 限制总字符数
                    for page_num in range(total_pages):
                        if len(text) > max_chars:
                            print(f"📄 已提取{page_num}页，达到字符限制，停止提取")
                            break

                        try:
                            page_text = pdf.pages[page_num].extract_text()
                            if page_text:
                                text += f"\n=== 第{page_num + 1}页 ===\n{page_text}\n"
                        except Exception as e:
                            print(f"⚠️ 第{page_num + 1}页提取失败: {e}")
                            continue

                if text.strip():
                    print(f"✅ pdfplumber提取成功，总字符数: {len(text)}")
                    return text.strip()
                else:
                    print("⚠️ pdfplumber提取的文本为空")

            except ImportError:
                print("⚠️ pdfplumber未安装")
            except Exception as e:
                print(f"⚠️ pdfplumber提取失败: {e}")

            # 方法1: 尝试使用PyPDF2
            try:
                import PyPDF2
                import io

                print("🔧 使用PyPDF2提取文本...")
                pdf_file = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                text = ""
                total_pages = len(pdf_reader.pages)
                print(f"📄 PDF总页数: {total_pages}")

                # 提取所有页面，但限制总长度
                max_chars = 50000  # 限制总字符数
                for page_num in range(total_pages):
                    if len(text) > max_chars:
                        print(f"📄 已提取{page_num}页，达到字符限制，停止提取")
                        break

                    try:
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n=== 第{page_num + 1}页 ===\n{page_text}\n"
                    except Exception as e:
                        print(f"⚠️ 第{page_num + 1}页提取失败: {e}")
                        continue

                if text.strip():
                    print(f"✅ PyPDF2提取成功，总字符数: {len(text)}")
                    return text.strip()
                else:
                    print("⚠️ PyPDF2提取的文本为空")

            except ImportError:
                print("⚠️ PyPDF2未安装")
            except Exception as e:
                print(f"⚠️ PyPDF2提取失败: {e}")

            # 方法3: 尝试使用pymupdf (fitz)
            try:
                import fitz  # PyMuPDF
                import io

                print("🔧 使用PyMuPDF提取文本...")
                pdf_file = io.BytesIO(pdf_content)
                doc = fitz.open(stream=pdf_file, filetype="pdf")

                text = ""
                total_pages = len(doc)
                print(f"📄 PDF总页数: {total_pages}")

                max_chars = 50000  # 限制总字符数
                for page_num in range(total_pages):
                    if len(text) > max_chars:
                        print(f"📄 已提取{page_num}页，达到字符限制，停止提取")
                        break

                    try:
                        page = doc[page_num]
                        page_text = page.get_text()
                        if page_text:
                            text += f"\n=== 第{page_num + 1}页 ===\n{page_text}\n"
                    except Exception as e:
                        print(f"⚠️ 第{page_num + 1}页提取失败: {e}")
                        continue

                doc.close()

                if text.strip():
                    print(f"✅ PyMuPDF提取成功，总字符数: {len(text)}")
                    return text.strip()
                else:
                    print("⚠️ PyMuPDF提取的文本为空")

            except ImportError:
                print("⚠️ PyMuPDF未安装")
            except Exception as e:
                print(f"⚠️ PyMuPDF提取失败: {e}")

            print("❌ 所有PDF文本提取方法都失败了")
            return ""

        except Exception as e:
            print(f"❌ PDF文本提取过程中发生异常: {e}")
            return ""

    def analyze_with_pdf_text(self, pdf_text: str, paper_title: str) -> str:
        """基于PDF文本内容进行分析"""
        if not self.api_key or self.api_key == 'your_api_key_here':
            raise Exception("请配置有效的DeepSeek API密钥")

        # 限制文本长度，避免超过API限制
        max_text_length = 50000  # 保留足够的token用于prompt和回复
        if len(pdf_text) > max_text_length:
            # 智能截取：优先保留开头和结尾部分
            start_part = pdf_text[:max_text_length // 2]
            end_part = pdf_text[-(max_text_length // 2):]
            pdf_text = start_part + "\n\n...[中间部分已截断]...\n\n" + end_part
            print(f"📄 文本过长，已截断到{len(pdf_text)}字符")

        analysis_prompt = f"""请对以下论文进行深度分析：

标题：{paper_title}

论文内容：
{pdf_text}

请按照以下结构进行详细分析：

## 1. 论文概述
- 研究背景和动机
- 主要研究问题
- 论文的核心贡献

## 2. 文章解决的问题
- 问题定义
- 问题的挑战
- 现有方法的不足

## 3. 技术方法的创新点
- 采用的主要技术和方法
- 方法的详细内容
- 创新点和技术亮点
- 与现有方法相比的创新点

## 4. 实验评估
- 实验设计和评估指标
- 数据集、对比算法选择，对比算法的论文来源
- 主要实验结果
- 与其他方法的比较

## 5. 优缺点分析
- 论文的主要优势
- 存在的不足和局限性
- 可能的改进方向

## 6. 总体评价
- 论文质量评估（1-10分）
- 推荐指数和理由
- 适合的读者群体

请用中文进行分析，要求专业、客观、深入。"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }

        try:
            print("🧠 正在调用DeepSeek API进行文本分析...")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=300
            )

            print(f"📡 API响应状态: {response.status_code}")
            response.raise_for_status()

            result = response.json()

            if 'choices' not in result or not result['choices']:
                raise Exception("API响应格式错误：缺少choices字段")

            analysis_result = result['choices'][0]['message']['content'].strip()
            print(f"✅ DeepSeek文本分析完成，生成内容长度: {len(analysis_result)}字符")

            return analysis_result

        except Exception as e:
            print(f"❌ DeepSeek文本分析失败: {e}")
            raise Exception(f"基于PDF文本的分析失败: {e}")

    def _analyze_title_only(self, paper_title: str) -> str:
        """仅基于标题进行分析（备用方案）"""
        print("🔄 使用标题进行基础分析...")

        simple_prompt = f"""请基于论文标题《{paper_title}》进行分析，包括：

## 1. 研究领域分析
- 判断论文所属的研究领域
- 分析研究主题和关键词

## 2. 可能的研究内容
- 基于标题推测可能的研究方法
- 分析可能涉及的技术和理论

## 3. 学术价值评估
- 评估研究的创新性
- 分析对相关领域的可能贡献

## 4. 建议
- 阅读建议
- 相关研究方向推荐

注意：此分析仅基于标题，具体内容需要阅读完整论文。"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": simple_prompt
                }
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
        except Exception as e:
            return f"基于标题《{paper_title}》的基础分析：\n\n由于技术限制，无法进行详细分析。建议手动阅读论文获取完整信息。\n\n分析时间：{time.strftime('%Y-%m-%d %H:%M:%S')}"

    def translate_text(self, text: str) -> str:
        """翻译文本"""
        if not self.api_key or self.api_key == 'your_api_key_here':
            raise Exception("请配置有效的DeepSeek API密钥")

        system_prompt = """你是专业的学术论文翻译专家。请将以下英文学术摘要翻译成中文，要求：
1. 保持学术严谨性和专业术语准确性
2. 确保翻译流畅自然，符合中文学术表达习惯
3. 保留原文逻辑结构和关键信息
4. 保持数字、百分比等数据原样"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
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

        except Exception as e:
            raise Exception(f"翻译失败: {e}")