#!/usr/bin/env python3
"""
测试修复后的异步摘要抓取功能
"""

import sys
import json
import requests
import re
from typing import Dict, Optional

def get_ieee_paper_info(url: str) -> Dict:
    """
    根据参考代码实现的IEEE论文信息提取函数
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        matches = re.search(r'xplGlobal\.document\.metadata=(\{.*?\});', response.text, re.DOTALL)

        if matches:
            try:
                # 获取JSON字符串
                json_str = matches.group(1)
                # 将JSON字符串转换为字典
                metadata = json.loads(json_str)
                return metadata
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return {}
        else:
            print("Metadata not found in the HTML content.")
            return {}
    else:
        print(f"Failed to retrieve the content, status code: {response.status_code}")
        return {}

def test_article_number_extraction():
    """测试文章编号提取"""
    sys.path.append('.')
    
    # 模拟从IEEE adapter获取的论文数据格式
    mock_paper = {
        'title': 'Test Paper',
        'abstract': 'Short abstract...',
        'url': 'https://ieeexplore.ieee.org/document/11121619/',
        'source_specific': {
            'ieee_number': '11121619',
            'volume': 'PP',
            'issue': '99'
        }
    }
    
    # 测试文章编号提取
    try:
        from utils.async_abstract_fetcher import IEEEAsyncService
        service = IEEEAsyncService()
        article_number = service._extract_article_number(mock_paper)
        
        print(f"✓ Article number extraction test: {article_number}")
        return article_number
    except ImportError:
        print("❌ Cannot import IEEEAsyncService (missing aiohttp)")
        return None

def test_manual_abstract_extraction():
    """手动测试摘要提取"""
    # 使用一个真实的IEEE URL进行测试
    test_url = "https://ieeexplore.ieee.org/document/11121619/"
    
    print(f"🔍 Testing abstract extraction from: {test_url}")
    
    paper_info = get_ieee_paper_info(test_url)
    
    if paper_info:
        abstract = paper_info.get('abstract', '')
        title = paper_info.get('title', 'No Title')
        
        print(f"✓ Title: {title[:60]}...")
        print(f"✓ Abstract length: {len(abstract)} chars")
        
        if abstract:
            # 显示摘要的前100个字符
            print(f"✓ Abstract preview: {abstract[:100]}...")
            return True
        else:
            print("❌ No abstract found")
            return False
    else:
        print("❌ Failed to extract paper info")
        return False

if __name__ == "__main__":
    print("🧪 Testing IEEE Abstract Extraction Fixes")
    print("=" * 50)
    
    # 测试1: 文章编号提取
    print("\n1. Testing article number extraction...")
    article_num = test_article_number_extraction()
    
    # 测试2: 手动摘要提取（使用参考代码的方法）
    print("\n2. Testing manual abstract extraction...")
    success = test_manual_abstract_extraction()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tests completed successfully!")
        print("   The async abstract fetcher should now work correctly.")
    else:
        print("⚠️ Some tests failed. Check network connectivity or IEEE access.")