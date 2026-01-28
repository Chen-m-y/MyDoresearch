"""
简单的API测试
"""

import sys
import os

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from config import Config


if __name__ == '__main__':
    # 简单的手动测试
    print("运行基本测试...")
    
    with app.test_client() as client:
        # 测试健康检查
        print("测试 /api/v1/health ...")
        response = client.get('/api/v1/health')
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.get_json()}")
        print()
        
        # 测试数据源列表
        print("测试 /api/v1/sources ...")
        response = client.get('/api/v1/sources')
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.get_json()}")
        print()
        
        # 测试无效抓取请求
        print("测试 /api/v1/fetch (无效请求) ...")
        response = client.post('/api/v1/fetch', json={
            'source': 'invalid_source',
            'source_params': {}
        })
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.get_json()}")
        
    print("测试完成!")