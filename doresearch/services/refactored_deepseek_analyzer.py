"""
重构后的DeepSeek分析器
向后兼容性包装器，实际实现已拆分到deepseek子模块中
"""

# 导入新模块的所有公共接口，保持向后兼容
from .deepseek import *