#!/usr/bin/env python3
"""
进度监控API测试脚本
"""

import requests
import time
import json

BASE_URL = "http://192.168.1.135:8000"

def test_progress_apis():
    """测试进度监控相关的API"""
    
    print("🧪 进度监控API测试")
    print("=" * 50)
    
    # 测试1: 查看当前任务统计
    print("\n1. 查看任务统计")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/progress/stats")
        if response.status_code == 200:
            stats = response.json()['data']
            print(f"✓ 任务统计: {stats}")
        else:
            print(f"✗ 获取统计失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    # 测试2: 查看所有任务
    print("\n2. 查看所有任务")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/progress/tasks")
        if response.status_code == 200:
            tasks = response.json()['data']
            print(f"✓ 当前任务数: {tasks['total_count']}")
            for task in tasks['tasks'][:3]:  # 只显示前3个
                print(f"  - 任务 {task['task_id']}: {task['status']} ({task['progress_percent']:.1f}%)")
        else:
            print(f"✗ 获取任务失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    # 测试3: 启动一个异步任务
    print("\n3. 启动异步IEEE抓取任务")
    try:
        payload = {
            "source": "ieee",
            "source_params": {
                "punumber": "32",
                "limit": 3,
                "fetch_full_abstract": True
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/fetch/async", json=payload)
        if response.status_code == 200:
            result = response.json()['data']
            task_id = result['task_id']
            print(f"✓ 异步任务已启动: {task_id}")
            print(f"  进度查询URL: {result['progress_url']}")
            
            # 监控任务进度
            print("\n监控任务进度:")
            for i in range(10):  # 最多监控10次
                time.sleep(2)  # 等待2秒
                
                progress_response = requests.get(f"{BASE_URL}/api/v1/progress/tasks/{task_id}")
                if progress_response.status_code == 200:
                    task = progress_response.json()['data']['task']
                    status = task['status']
                    progress = task['progress_percent']
                    operation = task['current_operation']
                    elapsed = task['elapsed_time']
                    
                    print(f"  [{i+1}] {status} - {progress:.1f}% - {operation} ({elapsed:.1f}s)")
                    
                    if status in ['completed', 'failed']:
                        if status == 'completed' and task.get('results'):
                            results = task['results']
                            print(f"  ✅ 任务完成! 抓取了 {results.get('papers_count', 0)} 篇论文")
                        elif status == 'failed':
                            print(f"  ❌ 任务失败: {task.get('error_message', '未知错误')}")
                        break
                else:
                    print(f"  ✗ 获取进度失败: {progress_response.status_code}")
                    break
            
        else:
            print(f"✗ 启动异步任务失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 异步任务测试失败: {e}")
    
    # 测试4: 查看正在运行的任务
    print("\n4. 查看正在运行的任务")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/progress/tasks/running")
        if response.status_code == 200:
            running_tasks = response.json()['data']
            print(f"✓ 正在运行的任务数: {running_tasks['count']}")
            for task in running_tasks['tasks']:
                print(f"  - {task['task_id']}: {task['current_operation']} ({task['progress_percent']:.1f}%)")
        else:
            print(f"✗ 获取运行任务失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 进度监控API测试完成!")

def test_basic_fetch():
    """测试基础的同步抓取"""
    print("\n📚 测试同步抓取 (传统方式)")
    try:
        payload = {
            "source": "ieee", 
            "source_params": {
                "punumber": "32",
                "limit": 2,
                "fetch_full_abstract": False  # 关闭完整摘要抓取，测试基础功能
            }
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/v1/fetch", json=payload)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            papers_count = len(result['data']['papers'])
            print(f"✓ 同步抓取完成: {papers_count} 篇论文 ({elapsed:.2f}s)")
            
            if papers_count > 0:
                paper = result['data']['papers'][0]
                print(f"  示例: {paper['title'][:60]}...")
        else:
            print(f"✗ 同步抓取失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 同步抓取测试失败: {e}")

if __name__ == "__main__":
    # 先测试基础功能
    test_basic_fetch()
    
    # 再测试进度监控
    test_progress_apis()