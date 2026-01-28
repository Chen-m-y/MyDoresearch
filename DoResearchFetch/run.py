#!/usr/bin/env python3
"""
应用启动脚本
支持加载环境变量
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量文件
load_dotenv()

# 导入Flask应用
from app import app

if __name__ == '__main__':
    # 从环境变量获取配置
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print(f"启动 Do Research Fetch 微服务...")
    print(f"地址: http://{host}:{port}")
    print(f"调试模式: {debug}")
    print(f"支持的数据源: IEEE")
    
    # 检查必要的环境变量
    ieee_api_key = os.getenv('IEEE_API_KEY')
    if not ieee_api_key:
        print("⚠️  警告: 未设置 IEEE_API_KEY，IEEE 适配器可能无法正常工作")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n服务已停止")