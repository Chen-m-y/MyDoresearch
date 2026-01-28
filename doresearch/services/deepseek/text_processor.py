"""
文本处理器模块
"""
from common.logging import get_logger


class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.TextProcessor")
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = " ".join(text.split())
        
        # 移除非打印字符
        text = "".join(char for char in text if char.isprintable() or char.isspace())
        
        return text.strip()
    
    def truncate_text(self, text: str, max_length: int) -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        
        # 尝试在句子边界截断
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclamation = truncated.rfind('!')
        
        sentence_end = max(last_period, last_question, last_exclamation)
        
        if sentence_end > max_length * 0.8:  # 如果句子结束位置在80%之后
            return truncated[:sentence_end + 1]
        else:
            return truncated + "..."
    
    def prepare_for_analysis(self, text: str, max_length: int) -> str:
        """为分析准备文本"""
        cleaned_text = self.clean_text(text)
        return self.truncate_text(cleaned_text, max_length)